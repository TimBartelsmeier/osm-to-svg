"""Shared validation helpers for geographic inputs."""


def validate_bbox(
    bbox: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    """Validate and normalize a geographic bounding box.

    Args:
        bbox: Bounding box as (min_lon, min_lat, max_lon, max_lat)

    Returns:
        The validated bounding box tuple.

    Raises:
        ValueError: If coordinate ranges or ordering are invalid.
    """
    min_lon, min_lat, max_lon, max_lat = bbox

    if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
        raise ValueError(f"Invalid longitude values: {min_lon}, {max_lon}")
    if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
        raise ValueError(f"Invalid latitude values: {min_lat}, {max_lat}")
    if min_lon >= max_lon:
        raise ValueError(f"min_lon ({min_lon}) must be less than max_lon ({max_lon})")
    if min_lat >= max_lat:
        raise ValueError(f"min_lat ({min_lat}) must be less than max_lat ({max_lat})")

    return (min_lon, min_lat, max_lon, max_lat)
