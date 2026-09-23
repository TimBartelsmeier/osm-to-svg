"""PBF parser facade."""

from collections.abc import Sequence
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
        validated_areas = (
            tuple(validate_bbox(area) for area in areas) if areas is not None else None
        )
        prepared_areas = (
            tuple(_prepare_area(area) for area in validated_areas)
            if validated_areas is not None
            else None
        )

        handler = FeatureHandler(spec)
        handler.apply_file(self.pbf_path, locations=True)

        if spec.needs_areas:
            handler.apply_file(self.pbf_path, locations=True, idx="flex_mem")

        unique_features: list[Feature] = []
        seen: set[
            tuple[tuple[tuple[float, float], ...], tuple[tuple[str, str], ...], bool]
        ] = set()

        for feature in handler.features:
            key = (
                tuple(feature.geometry),
                tuple(sorted(feature.tags.items())),
                feature.is_closed,
            )
            if key not in seen and self._matches_limit(
                feature, prepared_areas, object_ids
            ):
                seen.add(key)
                unique_features.append(feature)

        return unique_features

    @staticmethod
    def _matches_limit(
        feature: Feature,
        areas: Sequence[Polygon | _PreparedArea] | None,
        object_ids: frozenset[OsmObjectId] | set[OsmObjectId] | None,
    ) -> bool:
        if areas is None and object_ids is None:
            return True
        matches_area = areas is not None and any(
            _geometry_intersects_bbox(feature.geometry, area) for area in areas
        )
        matches_object_id = object_ids is not None and feature.object_id in object_ids
        return matches_area or matches_object_id


def _geometry_intersects_bbox(
    geometry: list[tuple[float, float]],
    bbox: Polygon | _PreparedArea,
) -> bool:
    area = (
        bbox if isinstance(bbox, _PreparedArea) else _prepare_area(validate_bbox(bbox))
    )
    return _geometry_intersects_area(geometry, area)


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
) -> bool:
    if not geometry:
        return False

    min_lat = min(point[0] for point in geometry)
    max_lat = max(point[0] for point in geometry)
    min_lon = min(point[1] for point in geometry)
    max_lon = max(point[1] for point in geometry)
    south, west, north, east = area.envelope
    if max_lat < south or min_lat > north or max_lon < west or min_lon > east:
        return False

    polygon = area.polygon

    if any(_point_in_polygon(point, polygon) for point in geometry):
        return True

    feature_edges = list(pairwise(geometry))
    if len(geometry) > 2 and geometry[0] != geometry[-1]:
        feature_edges.append((geometry[-1], geometry[0]))
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
