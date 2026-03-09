"""Geocoding utilities for converting place names to bounding boxes."""

import math

import httpx

from osm_to_svg.validation import validate_bbox


def _validate_positive_distance(name: str, value: float | None) -> None:
    if value is not None and value <= 0:
        raise ValueError(f"{name} must be greater than 0")


def _kilometers_per_longitude_degree(latitude: float) -> float:
    km = 111.0 * math.cos(math.radians(latitude))
    if abs(km) < 1e-9:
        raise ValueError(
            "Cannot build east/west bounding box at this latitude because "
            "longitude degrees approach zero length near the poles."
        )
    return km


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
    _validate_positive_distance("width_km", width_km)
    _validate_positive_distance("east_km", east_km)
    _validate_positive_distance("west_km", west_km)
    _validate_positive_distance("height_km", height_km)
    _validate_positive_distance("north_km", north_km)
    _validate_positive_distance("south_km", south_km)

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

    if width_km is not None:
        east_km = width_km / 2
        west_km = width_km / 2

    if height_km is not None:
        north_km = height_km / 2
        south_km = height_km / 2

    assert east_km is not None and west_km is not None
    assert north_km is not None and south_km is not None

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

    result = results[0]
    center_lat = float(result["lat"])
    center_lon = float(result["lon"])

    lat_degree_km = 111.0
    lon_degree_km = _kilometers_per_longitude_degree(center_lat)

    north_offset = north_km / lat_degree_km
    south_offset = south_km / lat_degree_km
    east_offset = east_km / lon_degree_km
    west_offset = west_km / lon_degree_km

    min_lat = center_lat - south_offset
    max_lat = center_lat + north_offset
    min_lon = center_lon - west_offset
    max_lon = center_lon + east_offset

    return validate_bbox((min_lon, min_lat, max_lon, max_lat))
