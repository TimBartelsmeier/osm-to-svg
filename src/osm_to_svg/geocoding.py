"""Geocoding utilities for converting place names to bounding boxes."""

import math

import httpx

from osm_to_svg.validation import validate_bbox


def get_bbox_from_place(
    place_name: str,
    *,
    width_km: float | None = None,
    east_km: float | None = None,
    west_km: float | None = None,
    height_km: float | None = None,
    north_km: float | None = None,
    south_km: float | None = None,
    timeout: int = 30,
) -> tuple[float, float, float, float]:
    """Get bounding box coordinates for a place by name with dimensions in kilometers.

    This function geocodes a place name using the Nominatim API and creates a bounding
    box around the returned center point with the specified dimensions in kilometers.

    For width, specify either:
    - width_km: Creates a symmetric box (extends equally east and west)
    - east_km and west_km: Creates an asymmetric box

    For height, specify either:
    - height_km: Creates a symmetric box (extends equally north and south)
    - north_km and south_km: Creates an asymmetric box

    Args:
        place_name: Name of the place to geocode (e.g., "Hannover, Germany")
        width_km: Total width in kilometers (symmetric, optional)
        east_km: Distance to extend east from center in km (optional)
        west_km: Distance to extend west from center in km (optional)
        height_km: Total height in kilometers (symmetric, optional)
        north_km: Distance to extend north from center in km (optional)
        south_km: Distance to extend south from center in km (optional)
        timeout: Request timeout in seconds (default: 30)

    Returns:
        Bounding box as (min_lon, min_lat, max_lon, max_lat)

    Raises:
        ValueError: If place not found, invalid parameter combinations, or API error
        httpx.HTTPError: If the geocoding request fails

    Example:
        >>> # Symmetric bounding box
        >>> bbox = get_bbox_from_place("Hannover, Germany", width_km=10, height_km=10)
        >>> # Asymmetric bounding box
        >>> bbox = get_bbox_from_place(
        ...     "Berlin",
        ...     east_km=15,
        ...     west_km=10,
        ...     north_km=12,
        ...     south_km=8
        ... )
    """
    # Validate parameter combinations
    if width_km is not None and (east_km is not None or west_km is not None):
        raise ValueError(
            "Cannot specify both width_km and east_km/west_km. "
            "Use either width_km for symmetric or east_km/west_km for asymmetric."
        )

    if height_km is not None and (north_km is not None or south_km is not None):
        raise ValueError(
            "Cannot specify both height_km and north_km/south_km. "
            "Use either height_km for symmetric or north_km/south_km for asymmetric."
        )

    if width_km is None and (east_km is None or west_km is None):
        raise ValueError("Must specify either width_km or both east_km and west_km")

    if height_km is None and (north_km is None or south_km is None):
        raise ValueError("Must specify either height_km or both north_km and south_km")

    # Convert symmetric to asymmetric for consistent handling
    if width_km is not None:
        east_km = width_km / 2
        west_km = width_km / 2

    if height_km is not None:
        north_km = height_km / 2
        south_km = height_km / 2

    assert east_km is not None and west_km is not None
    assert north_km is not None and south_km is not None

    # Geocode the place name using Nominatim
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": place_name,
        "format": "json",
        "limit": 1,
    }
    headers = {
        "User-Agent": "osm-to-svg Python library (https://github.com/timbartelsmeier/osm-to-svg)"
    }

    try:
        response = httpx.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        results = response.json()
    except httpx.HTTPError as e:
        raise httpx.HTTPError(f"Failed to geocode '{place_name}': {e}") from e

    if not results:
        raise ValueError(
            f"Could not find location for '{place_name}'. "
            "Try being more specific (e.g., include country or region)."
        )

    # Extract center coordinates
    result = results[0]
    center_lat = float(result["lat"])
    center_lon = float(result["lon"])

    # Calculate bounding box
    # For latitude: 1 degree ≈ 111 km (constant)
    lat_degree_km = 111.0

    # For longitude: 1 degree ≈ 111 km * cos(latitude)
    lon_degree_km = 111.0 * math.cos(math.radians(center_lat))

    # Calculate offsets in degrees
    north_offset = north_km / lat_degree_km
    south_offset = south_km / lat_degree_km
    east_offset = east_km / lon_degree_km
    west_offset = west_km / lon_degree_km

    # Calculate bounding box coordinates
    min_lat = center_lat - south_offset
    max_lat = center_lat + north_offset
    min_lon = center_lon - west_offset
    max_lon = center_lon + east_offset

    return validate_bbox((min_lon, min_lat, max_lon, max_lat))
