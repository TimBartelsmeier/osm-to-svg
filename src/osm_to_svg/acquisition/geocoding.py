"""Geocoding utilities for converting place names to coordinates."""

import httpx

from osm_to_svg.models import OsmObjectId


def _geocode_result(place_name: str, timeout: int) -> dict[str, object]:
    """Return the first Nominatim result for a place name."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": place_name, "format": "json", "limit": 1}
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
    return results[0]


def geocode_coordinates(
    place_name: str,
    *,
    timeout: int = 30,
) -> tuple[float, float]:
    """Geocode a place name and return its coordinates via Nominatim.

    Args:
        place_name: Human-readable place name to look up (e.g. ``"Hannover, Germany"``).
        timeout: HTTP request timeout in seconds (default: 30).

    Returns:
        ``(latitude, longitude)`` of the first result returned by Nominatim.

    Raises:
        ValueError: If no result is found for the given place name.
        httpx.HTTPError: If the Nominatim request fails.
    """
    result = _geocode_result(place_name, timeout)
    return float(result["lat"]), float(result["lon"])


def geocode_osm_object(
    place_name: str,
    *,
    timeout: int = 30,
) -> OsmObjectId:
    """Geocode a place name and return its typed OSM object ID via Nominatim."""
    result = _geocode_result(place_name, timeout)
    object_type = result.get("osm_type")
    object_id = result.get("osm_id")
    if object_type not in {"node", "way", "relation"} or not isinstance(
        object_id, (int, str)
    ):
        raise ValueError(
            f"Nominatim result for '{place_name}' has no valid OSM object identity"
        )
    try:
        return OsmObjectId(object_type, int(object_id))
    except (TypeError, ValueError) as e:
        raise ValueError(
            f"Nominatim result for '{place_name}' has no valid OSM object identity"
        ) from e
