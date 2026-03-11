"""Geocoding utilities for converting place names to coordinates."""

import httpx


def geocode_place(
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
    return float(result["lat"]), float(result["lon"])
