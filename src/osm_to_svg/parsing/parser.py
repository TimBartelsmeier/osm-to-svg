"""PBF parser facade."""

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from itertools import pairwise

from pyproj import Geod

from osm_to_svg.features import FeatureSpec
from osm_to_svg.models import (
    AreaMatchMode,
    BoundingBox,
    Coordinate,
    Feature,
    FeatureFilter,
    Polygon,
)
from osm_to_svg.parsing.handlers import BoundsHandler, FeatureHandler
from osm_to_svg.validation import validate_bbox

_GEOD = Geod(ellps="WGS84")


@dataclass(frozen=True)
class _PreparedArea:
    polygon: Polygon
    envelope: BoundingBox
    edges: tuple[tuple[Coordinate, Coordinate], ...]


@dataclass(frozen=True)
class FeatureQuery:
    """Normalized extraction request used by shared parser traversals."""

    spec: FeatureSpec
    filter: FeatureFilter | None = None


@dataclass(frozen=True)
class _CompiledQuery:
    clauses: tuple[tuple[tuple[str, frozenset[str]], ...], ...]
    candidate_values: tuple[tuple[str, frozenset[str]], ...]


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
        filter: FeatureFilter | None = None,
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
            [
                FeatureQuery(
                    spec=spec,
                    filter=filter,
                )
            ]
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

        prepared_include_areas = tuple(
            tuple(_prepare_area(validate_bbox(area)) for area in query.filter.areas)
            if query.filter is not None and query.filter.areas is not None
            else None
            for query in normalized_queries
        )
        prepared_exclude_areas = tuple(
            tuple(
                _prepare_area(validate_bbox(area))
                for area in query.filter.exclude_areas
            )
            if query.filter is not None and query.filter.exclude_areas is not None
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
        compiled_queries = tuple(
            _compile_query(query.spec) for query in normalized_queries
        )
        candidate_index, wildcard_indexes = _build_candidate_index(compiled_queries)
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
                indexes = _candidate_query_indexes(
                    feature.tags, candidate_index, wildcard_indexes
                )
                if allowed_indexes is not None:
                    indexes &= allowed_indexes
                for index in indexes:
                    query = normalized_queries[index]
                    if key in seen[index] or not _matches_compiled_query(
                        compiled_queries[index], feature.tags
                    ):
                        continue
                    if not self._matches_limit(
                        feature,
                        prepared_include_areas[index],
                        prepared_exclude_areas[index],
                        query.filter.area_match_mode
                        if query.filter is not None
                        else "intersects",
                    ):
                        continue
                    if not self._matches_measurement_filter(feature, query.filter):
                        continue
                    seen[index].add(key)
                    results[index].append(feature)

        return results

    @staticmethod
    def _matches_measurement_filter(
        feature: Feature,
        feature_filter: FeatureFilter | None,
    ) -> bool:
        """Return whether a feature satisfies its applicable metric limits."""
        if feature_filter is None:
            return True

        if feature.is_closed:
            if (
                feature_filter.minimum_area is None
                and feature_filter.maximum_area is None
            ):
                return True
            longitudes = [point[1] for point in feature.geometry]
            latitudes = [point[0] for point in feature.geometry]
            area, _ = _GEOD.polygon_area_perimeter(longitudes, latitudes)
            area = abs(area)
            return _within_limits(
                area,
                feature_filter.minimum_area,
                feature_filter.maximum_area,
            )

        if (
            feature_filter.minimum_length is None
            and feature_filter.maximum_length is None
        ):
            return True
        longitudes = [point[1] for point in feature.geometry]
        latitudes = [point[0] for point in feature.geometry]
        length = _GEOD.line_length(longitudes, latitudes)
        return _within_limits(
            length,
            feature_filter.minimum_length,
            feature_filter.maximum_length,
        )

    @staticmethod
    def _matches_limit(
        feature: Feature,
        include_areas: Sequence[Polygon | _PreparedArea] | None,
        exclude_areas: Sequence[Polygon | _PreparedArea] | None = None,
        area_match_mode: AreaMatchMode = "intersects",
    ) -> bool:
        if include_areas is None and exclude_areas is None:
            return True
        feature_envelope = _geometry_envelope(feature.geometry)
        feature_edges = _geometry_edges(feature.geometry)
        matches_area = include_areas is None or any(
            _geometry_matches_area(
                feature.geometry,
                area if isinstance(area, _PreparedArea) else _prepare_area(area),
                area_match_mode=area_match_mode,
                feature_envelope=feature_envelope,
                feature_edges=feature_edges,
            )
            for area in include_areas
        )
        matches_excluded_area = exclude_areas is not None and any(
            _geometry_matches_area(
                feature.geometry,
                area if isinstance(area, _PreparedArea) else _prepare_area(area),
                area_match_mode=area_match_mode,
                feature_envelope=feature_envelope,
                feature_edges=feature_edges,
            )
            for area in exclude_areas
        )
        return matches_area and not matches_excluded_area


def _matches_spec(spec: FeatureSpec, tags: dict[str, str]) -> bool:
    """Return whether tags satisfy at least one feature-spec clause."""
    return _matches_compiled_query(_compile_query(spec), tags)


def _within_limits(
    value: float,
    minimum: float | None,
    maximum: float | None,
) -> bool:
    return (minimum is None or value >= minimum) and (
        maximum is None or value <= maximum
    )


def _compile_query(spec: FeatureSpec) -> _CompiledQuery:
    clauses = tuple(
        tuple((key, frozenset(values)) for key, values in clause.items())
        for clause in spec.match_clauses
    )
    candidate_values = tuple(
        (key, frozenset(values))
        for clause in clauses
        for key, values in (min(clause, key=lambda item: len(item[1])),)
        if clause
    )
    return _CompiledQuery(clauses=clauses, candidate_values=candidate_values)


def _candidate_query_indexes(
    tags: dict[str, str],
    candidate_index: dict[tuple[str, str], set[int]],
    wildcard_indexes: set[int],
) -> set[int]:
    """Return queries whose clauses have at least one potentially matching tag."""
    candidates = set(wildcard_indexes)
    for key, value in tags.items():
        candidates.update(candidate_index.get((key, value), ()))
    return candidates


def _build_candidate_index(
    compiled_queries: Sequence[_CompiledQuery],
) -> tuple[dict[tuple[str, str], set[int]], set[int]]:
    candidate_index: dict[tuple[str, str], set[int]] = {}
    wildcard_indexes: set[int] = set()
    for index, query in enumerate(compiled_queries):
        if any(not clause for clause in query.clauses):
            wildcard_indexes.add(index)
        for key, values in query.candidate_values:
            for value in values:
                candidate_index.setdefault((key, value), set()).add(index)
    return candidate_index, wildcard_indexes


def _matches_compiled_query(query: _CompiledQuery, tags: dict[str, str]) -> bool:
    return any(
        all(tags.get(tag_key) in valid_values for tag_key, valid_values in clause)
        for clause in query.clauses
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


def _geometry_matches_area(
    geometry: list[tuple[float, float]],
    area: _PreparedArea,
    *,
    area_match_mode: AreaMatchMode,
    feature_envelope: BoundingBox | None = None,
    feature_edges: Sequence[tuple[Coordinate, Coordinate]] | None = None,
) -> bool:
    if area_match_mode == "intersects":
        return _geometry_intersects_area(
            geometry,
            area,
            feature_envelope=feature_envelope,
            feature_edges=feature_edges,
        )
    return _geometry_is_contained_in_area(
        geometry,
        area,
        feature_envelope=feature_envelope,
        feature_edges=feature_edges,
    )


def _geometry_is_contained_in_area(
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
    if min_lat < south or max_lat > north or min_lon < west or max_lon > east:
        return False
    if not all(_point_in_polygon(point, area.polygon) for point in geometry):
        return False
    if feature_edges is None:
        feature_edges = _geometry_edges(geometry)
    return all(_segment_is_contained(start, end, area) for start, end in feature_edges)


def _segment_is_contained(
    start: Coordinate,
    end: Coordinate,
    area: _PreparedArea,
) -> bool:
    delta_lat = end[0] - start[0]
    delta_lon = end[1] - start[1]
    parameters = [0.0, 1.0]
    for edge_start, edge_end in area.edges:
        edge_delta_lat = edge_end[0] - edge_start[0]
        edge_delta_lon = edge_end[1] - edge_start[1]
        denominator = delta_lat * edge_delta_lon - delta_lon * edge_delta_lat
        if denominator == 0:
            continue
        offset_lat = edge_start[0] - start[0]
        offset_lon = edge_start[1] - start[1]
        parameter = (
            offset_lat * edge_delta_lon - offset_lon * edge_delta_lat
        ) / denominator
        edge_parameter = (offset_lat * delta_lon - offset_lon * delta_lat) / denominator
        if 0 <= parameter <= 1 and 0 <= edge_parameter <= 1:
            parameters.append(parameter)
    parameters.sort()
    return all(
        _point_in_polygon(
            (
                start[0] + delta_lat * (first + second) / 2,
                start[1] + delta_lon * (first + second) / 2,
            ),
            area.polygon,
        )
        for first, second in pairwise(parameters)
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
