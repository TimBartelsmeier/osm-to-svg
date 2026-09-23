"""PBF parser facade."""

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from itertools import pairwise

from osm_to_svg.features import FeatureSpec
from osm_to_svg.models import BoundingBox, Coordinate, Feature, OsmObjectId, Polygon
from osm_to_svg.parsing.handlers import BoundsHandler, FeatureHandler
from osm_to_svg.validation import validate_bbox


@dataclass(frozen=True)
class _PreparedArea:
    polygon: Polygon
    envelope: BoundingBox
    edges: tuple[tuple[Coordinate, Coordinate], ...]


@dataclass(frozen=True)
class FeatureQuery:
    """Normalized extraction request used by shared parser traversals."""

    spec: FeatureSpec
    areas: Sequence[Polygon] | None = None
    object_ids: frozenset[OsmObjectId] | set[OsmObjectId] | None = None


class PBFParser:
    """Parser for OpenStreetMap PBF files."""

    def __init__(self, pbf_path: str):
        """Initialize the parser with the path to a PBF file."""
        self.pbf_path = pbf_path

    def get_bounds(self) -> BoundingBox:
        """Scan all nodes in the PBF file and return the geographic bounding box.

        Returns:
            Bounding box as ``(south_lat, west_lon, north_lat, east_lon)``.
        """
        handler = BoundsHandler()
        handler.apply_file(self.pbf_path, locations=True)
        return handler.get_bounds()

    def extract_features(
        self,
        spec: FeatureSpec,
        *,
        areas: Sequence[Polygon] | None = None,
        object_ids: frozenset[OsmObjectId] | set[OsmObjectId] | None = None,
    ) -> list[Feature]:
        """Extract OSM features matching the given spec from the PBF file.

        Deduplicates the results so each unique geometry appears only once.
        If ``spec.needs_areas`` is True, the file is processed a second time
        with area indexing enabled to capture multipolygon relations.

        Args:
            spec: Feature specification describing the OSM tag filters.

        Returns:
            List of unique :class:`~osm_to_svg.models.Feature` objects.
        """
        return self.extract_features_for_queries(
            [FeatureQuery(spec=spec, areas=areas, object_ids=object_ids)]
        )[0]

    def extract_features_for_queries(
        self,
        queries: Iterable[FeatureQuery],
        _progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[list[Feature]]:
        """Extract multiple layer queries during shared PBF traversals."""
        normalized_queries = tuple(queries)
        if not normalized_queries:
            return []

        combined_spec = normalized_queries[0].spec
        for query in normalized_queries[1:]:
            combined_spec = combined_spec | query.spec

        prepared_areas = tuple(
            tuple(_prepare_area(validate_bbox(area)) for area in query.areas)
            if query.areas is not None
            else None
            for query in normalized_queries
        )
        handler = FeatureHandler(combined_spec)
        handler.apply_file(self.pbf_path, locations=True)
        if _progress_callback is not None:
            _progress_callback(
                1,
                2 if any(query.spec.needs_areas for query in normalized_queries) else 1,
            )
        feature_batches: list[tuple[Iterable[Feature], set[int] | None]] = [
            (handler.features, None)
        ]

        area_query_indexes = {
            index
            for index, query in enumerate(normalized_queries)
            if query.spec.needs_areas
        }
        if area_query_indexes:
            area_spec = normalized_queries[next(iter(area_query_indexes))].spec
            for index in sorted(area_query_indexes)[1:]:
                area_spec = area_spec | normalized_queries[index].spec
            area_handler = FeatureHandler(area_spec)
            area_handler.apply_file(self.pbf_path, locations=True, idx="flex_mem")
            if _progress_callback is not None:
                _progress_callback(2, 2)
            feature_batches.append((area_handler.features, area_query_indexes))

        results: list[list[Feature]] = [[] for _ in normalized_queries]
        seen: list[
            set[
                tuple[
                    tuple[tuple[float, float], ...], tuple[tuple[str, str], ...], bool
                ]
            ]
        ] = [set() for _ in normalized_queries]
        for batch, allowed_indexes in feature_batches:
            for feature in batch:
                key = (
                    tuple(feature.geometry),
                    tuple(sorted(feature.tags.items())),
                    feature.is_closed,
                )
                indexes = (
                    range(len(normalized_queries))
                    if allowed_indexes is None
                    else allowed_indexes
                )
                for index in indexes:
                    query = normalized_queries[index]
                    if key in seen[index] or not _matches_spec(
                        query.spec, feature.tags
                    ):
                        continue
                    if not self._matches_limit(
                        feature, prepared_areas[index], query.object_ids
                    ):
                        continue
                    seen[index].add(key)
                    results[index].append(feature)

        return results

    @staticmethod
    def _matches_limit(
        feature: Feature,
        areas: Sequence[Polygon | _PreparedArea] | None,
        object_ids: frozenset[OsmObjectId] | set[OsmObjectId] | None,
    ) -> bool:
        if areas is None and object_ids is None:
            return True
        feature_envelope = _geometry_envelope(feature.geometry)
        feature_edges = _geometry_edges(feature.geometry)
        matches_area = areas is not None and any(
            _geometry_intersects_area(
                feature.geometry,
                area if isinstance(area, _PreparedArea) else _prepare_area(area),
                feature_envelope=feature_envelope,
                feature_edges=feature_edges,
            )
            for area in areas
        )
        matches_object_id = object_ids is not None and feature.object_id in object_ids
        return matches_area or matches_object_id


def _matches_spec(spec: FeatureSpec, tags: dict[str, str]) -> bool:
    """Return whether tags satisfy at least one feature-spec clause."""
    return any(
        all(
            tags.get(tag_key) in valid_values
            for tag_key, valid_values in clause.items()
        )
        for clause in spec.match_clauses
    )


def _geometry_intersects_bbox(
    geometry: list[tuple[float, float]],
    bbox: Polygon | _PreparedArea,
) -> bool:
    area = (
        bbox if isinstance(bbox, _PreparedArea) else _prepare_area(validate_bbox(bbox))
    )
    return _geometry_intersects_area(geometry, area)


def _geometry_envelope(geometry: list[tuple[float, float]]) -> BoundingBox:
    """Return a feature envelope for reuse across area checks."""
    latitudes = [point[0] for point in geometry]
    longitudes = [point[1] for point in geometry]
    return (
        min(latitudes),
        min(longitudes),
        max(latitudes),
        max(longitudes),
    )


def _geometry_edges(
    geometry: list[tuple[float, float]],
) -> tuple[tuple[Coordinate, Coordinate], ...]:
    """Return the edges used by exact intersection checks."""
    if len(geometry) < 2:
        return ()
    edges = list(pairwise(geometry))
    if len(geometry) > 2 and geometry[0] != geometry[-1]:
        edges.append((geometry[-1], geometry[0]))
    return tuple(edges)


def _prepare_area(polygon: Polygon) -> _PreparedArea:
    latitudes = [point[0] for point in polygon]
    longitudes = [point[1] for point in polygon]
    return _PreparedArea(
        polygon=polygon,
        envelope=(
            min(latitudes),
            min(longitudes),
            max(latitudes),
            max(longitudes),
        ),
        edges=tuple(pairwise(polygon)),
    )


def _geometry_intersects_area(
    geometry: list[tuple[float, float]],
    area: _PreparedArea,
    *,
    feature_envelope: BoundingBox | None = None,
    feature_edges: Sequence[tuple[Coordinate, Coordinate]] | None = None,
) -> bool:
    if not geometry:
        return False

    if feature_envelope is None:
        feature_envelope = _geometry_envelope(geometry)
    min_lat, min_lon, max_lat, max_lon = feature_envelope
    south, west, north, east = area.envelope
    if max_lat < south or min_lat > north or max_lon < west or min_lon > east:
        return False

    polygon = area.polygon

    if any(_point_in_polygon(point, polygon) for point in geometry):
        return True

    if feature_edges is None:
        feature_edges = _geometry_edges(geometry)
    if any(
        _segments_intersect(start, end, polygon_start, polygon_end)
        for start, end in feature_edges
        for polygon_start, polygon_end in area.edges
    ):
        return True

    return bool(
        geometry
        and geometry[0] == geometry[-1]
        and _point_in_polygon(polygon[0], geometry)
    )


def _segments_intersect(
    start: tuple[float, float],
    end: tuple[float, float],
    other_start: tuple[float, float],
    other_end: tuple[float, float],
) -> bool:
    def orientation(
        a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]
    ) -> float:
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def on_segment(
        a: tuple[float, float],
        b: tuple[float, float],
        point: tuple[float, float],
    ) -> bool:
        return min(a[0], b[0]) <= point[0] <= max(a[0], b[0]) and min(
            a[1], b[1]
        ) <= point[1] <= max(a[1], b[1])

    orientations = (
        orientation(start, end, other_start),
        orientation(start, end, other_end),
        orientation(other_start, other_end, start),
        orientation(other_start, other_end, end),
    )
    if orientations[0] == 0 and on_segment(start, end, other_start):
        return True
    if orientations[1] == 0 and on_segment(start, end, other_end):
        return True
    if orientations[2] == 0 and on_segment(other_start, other_end, start):
        return True
    if orientations[3] == 0 and on_segment(other_start, other_end, end):
        return True

    return (orientations[0] > 0) != (orientations[1] > 0) and (orientations[2] > 0) != (
        orientations[3] > 0
    )


def _point_in_polygon(
    point: tuple[float, float], polygon: list[tuple[float, float]] | Polygon
) -> bool:
    lat, lon = point
    inside = False
    for start, end in pairwise(polygon):
        if _point_on_segment(start, end, point):
            return True
        if (start[1] > lon) != (end[1] > lon):
            crossing_lat = (end[0] - start[0]) * (lon - start[1]) / (
                end[1] - start[1]
            ) + start[0]
            if lat < crossing_lat:
                inside = not inside
    return inside


def _point_on_segment(
    start: tuple[float, float],
    end: tuple[float, float],
    point: tuple[float, float],
) -> bool:
    cross = (end[0] - start[0]) * (point[1] - start[1]) - (end[1] - start[1]) * (
        point[0] - start[0]
    )
    return (
        cross == 0
        and min(start[0], end[0]) <= point[0] <= max(start[0], end[0])
        and min(start[1], end[1]) <= point[1] <= max(start[1], end[1])
    )


_segments_intersect_bbox = _segments_intersect
