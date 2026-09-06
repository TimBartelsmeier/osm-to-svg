"""PBF parser facade."""

from collections.abc import Sequence

from osm_to_svg.features import FeatureSpec
from osm_to_svg.models import BoundingBox, Feature, OsmObjectId
from osm_to_svg.parsing.handlers import BoundsHandler, FeatureHandler


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
        bboxes: Sequence[BoundingBox] | None = None,
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
        if bboxes is not None and object_ids is not None:
            raise ValueError("Specify either bboxes or object_ids, not both")

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
            if key not in seen and self._matches_limit(feature, bboxes, object_ids):
                seen.add(key)
                unique_features.append(feature)

        return unique_features

    @staticmethod
    def _matches_limit(
        feature: Feature,
        bboxes: Sequence[BoundingBox] | None,
        object_ids: frozenset[OsmObjectId] | set[OsmObjectId] | None,
    ) -> bool:
        if object_ids is not None:
            return feature.object_id in object_ids
        if bboxes is None:
            return True
        return any(_geometry_intersects_bbox(feature.geometry, bbox) for bbox in bboxes)


def _geometry_intersects_bbox(
    geometry: list[tuple[float, float]],
    bbox: BoundingBox,
) -> bool:
    south, west, north, east = bbox

    def inside(point: tuple[float, float]) -> bool:
        lat, lon = point
        return south <= lat <= north and west <= lon <= east

    if any(inside(point) for point in geometry):
        return True

    edges = list(zip(geometry, geometry[1:]))
    if len(geometry) > 2 and geometry[0] != geometry[-1]:
        edges.append((geometry[-1], geometry[0]))

    for start, end in edges:
        if _segments_intersect_bbox(start, end, bbox):
            return True

    return bool(
        geometry
        and geometry[0] == geometry[-1]
        and _point_in_polygon((south, west), geometry)
    )


def _segments_intersect_bbox(
    start: tuple[float, float],
    end: tuple[float, float],
    bbox: BoundingBox,
) -> bool:
    south, west, north, east = bbox

    def orientation(
        a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]
    ) -> float:
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def intersects(
        a: tuple[float, float],
        b: tuple[float, float],
        c: tuple[float, float],
        d: tuple[float, float],
    ) -> bool:
        first = orientation(a, b, c) * orientation(a, b, d)
        second = orientation(c, d, a) * orientation(c, d, b)
        return first <= 0 and second <= 0

    rectangle = [(south, west), (south, east), (north, east), (north, west)]
    return any(
        intersects(start, end, corner, rectangle[(index + 1) % 4])
        for index, corner in enumerate(rectangle)
    )


def _point_in_polygon(
    point: tuple[float, float], polygon: list[tuple[float, float]]
) -> bool:
    lat, lon = point
    inside = False
    for start, end in zip(polygon, polygon[1:]):
        if (start[1] > lon) != (end[1] > lon):
            crossing_lat = (end[0] - start[0]) * (lon - start[1]) / (
                end[1] - start[1]
            ) + start[0]
            if lat < crossing_lat:
                inside = not inside
    return inside
