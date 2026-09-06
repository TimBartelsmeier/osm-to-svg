"""Shared validation helpers for geographic inputs."""

from osm_to_svg.models import BoundingBox


def validate_bbox(
    bbox: BoundingBox,
) -> BoundingBox:
    """Validate and normalize a geographic bounding box.

    Args:
        bbox: Bounding box as (south_lat, west_lon, north_lat, east_lon).

    Returns:
        The validated bounding box tuple.

    Raises:
        ValueError: If coordinate ranges or ordering are invalid.
    """
    south_lat, west_lon, north_lat, east_lon = bbox

    if not (-90 <= south_lat <= 90 and -90 <= north_lat <= 90):
        raise ValueError(f"Invalid latitude values: {south_lat}, {north_lat}")
    if not (-180 <= west_lon <= 180 and -180 <= east_lon <= 180):
        raise ValueError(f"Invalid longitude values: {west_lon}, {east_lon}")
    if south_lat >= north_lat:
        raise ValueError(
            f"south_lat ({south_lat}) must be less than north_lat ({north_lat})"
        )
    if west_lon >= east_lon:
        raise ValueError(
            f"west_lon ({west_lon}) must be less than east_lon ({east_lon})"
        )

    return (south_lat, west_lon, north_lat, east_lon)
