"""Shared validation helpers for geographic inputs."""

import math
from collections.abc import Sequence

from osm_to_svg.models import BoundingBox, Coordinate, Polygon


def validate_bbox(
    bbox: Sequence[Sequence[float]],
) -> Polygon:
    """Validate and normalize a geographic polygon.

    Args:
        bbox: Polygon vertices as ``(latitude, longitude)`` pairs.

    Returns:
        A closed, immutable polygon tuple.

    Raises:
        ValueError: If the polygon is malformed, degenerate, or self-intersecting.
    """
    try:
        coordinates = [tuple(vertex) for vertex in bbox]
    except (TypeError, ValueError) as error:
        raise ValueError(
            "bbox must be a sequence of latitude/longitude pairs"
        ) from error

    if coordinates and coordinates[0] == coordinates[-1]:
        coordinates.pop()
    if len(coordinates) < 3 or len(set(coordinates)) < 3:
        raise ValueError("bbox must contain at least three distinct vertices")

    normalized: list[Coordinate] = []
    for vertex in coordinates:
        if len(vertex) != 2:
            raise ValueError(
                "bbox vertices must contain exactly latitude and longitude"
            )
        latitude, longitude = vertex
        if not (math.isfinite(latitude) and math.isfinite(longitude)):
            raise ValueError("bbox coordinates must be finite")
        if not -90 <= latitude <= 90:
            raise ValueError(f"Invalid latitude value: {latitude}")
        if not -180 <= longitude <= 180:
            raise ValueError(f"Invalid longitude value: {longitude}")
        normalized.append((latitude, longitude))

    if _has_self_intersection(normalized):
        raise ValueError("bbox must not self-intersect")

    area = sum(
        start[0] * end[1] - end[0] * start[1]
        for start, end in zip(normalized, normalized[1:] + normalized[:1])
    )
    if area == 0:
        raise ValueError("bbox must enclose a nonzero area")

    return tuple(normalized + [normalized[0]])


def bbox_envelope(polygon: Polygon) -> BoundingBox:
    """Return the rectangular envelope of a validated polygon."""
    validated = validate_bbox(polygon)
    latitudes = [coordinate[0] for coordinate in validated]
    longitudes = [coordinate[1] for coordinate in validated]
    return (min(latitudes), min(longitudes), max(latitudes), max(longitudes))


def rectangle_to_polygon(bounds: BoundingBox) -> Polygon:
    """Convert legacy ``(south, west, north, east)`` bounds to a polygon."""
    south, west, north, east = bounds
    return validate_bbox(((south, west), (south, east), (north, east), (north, west)))


def _has_self_intersection(polygon: list[Coordinate]) -> bool:
    edges = list(zip(polygon, polygon[1:] + polygon[:1]))
    for first_index, first_edge in enumerate(edges):
        for second_index in range(first_index + 1, len(edges)):
            if second_index in {first_index - 1, first_index + 1}:
                continue
            if first_index == 0 and second_index == len(edges) - 1:
                continue
            if _segments_intersect(*first_edge, *edges[second_index]):
                return True
    return False


def _segments_intersect(
    start_a: Coordinate,
    end_a: Coordinate,
    start_b: Coordinate,
    end_b: Coordinate,
) -> bool:
    def orientation(a: Coordinate, b: Coordinate, c: Coordinate) -> float:
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def on_segment(a: Coordinate, b: Coordinate, point: Coordinate) -> bool:
        return min(a[0], b[0]) <= point[0] <= max(a[0], b[0]) and min(
            a[1], b[1]
        ) <= point[1] <= max(a[1], b[1])

    orientations = (
        orientation(start_a, end_a, start_b),
        orientation(start_a, end_a, end_b),
        orientation(start_b, end_b, start_a),
        orientation(start_b, end_b, end_a),
    )
    if orientations[0] == 0 and on_segment(start_a, end_a, start_b):
        return True
    if orientations[1] == 0 and on_segment(start_a, end_a, end_b):
        return True
    if orientations[2] == 0 and on_segment(start_b, end_b, start_a):
        return True
    if orientations[3] == 0 and on_segment(start_b, end_b, end_a):
        return True
    return (orientations[0] > 0) != (orientations[1] > 0) and (orientations[2] > 0) != (
        orientations[3] > 0
    )
