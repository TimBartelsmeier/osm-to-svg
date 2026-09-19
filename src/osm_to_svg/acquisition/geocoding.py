"""Geocoding utilities for converting place names to coordinates."""

import httpx

from osm_to_svg.models import OsmObjectId, Polygon
from osm_to_svg.validation import validate_bbox


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


def get_polygon_from_osm_id(
    osm_id: OsmObjectId,
    *,
    timeout: int = 30,
) -> Polygon:
    """Fetch and validate the outer polygon of an OSM object from Nominatim.

    Args:
        osm_id: Typed OSM object identity to look up.
        timeout: HTTP request timeout in seconds (default: 30).

    Returns:
        The object's outer polygon as closed ``(latitude, longitude)`` vertices.

    Raises:
        TypeError: If the returned GeoJSON ring has an invalid container type.
        ValueError: If the object has no polygon geometry, has holes, or is a
            multipolygon. These geometries cannot be represented by ``Polygon``.
        httpx.HTTPError: If the Nominatim request fails.
    """
    url = "https://nominatim.openstreetmap.org/details"
    params = {
        "osmtype": osm_id.object_type[0].upper(),
        "osmid": osm_id.object_id,
        "format": "json",
        "polygon_geojson": 1,
    }
    headers = {
        "User-Agent": "osm-to-svg Python library (https://github.com/timbartelsmeier/osm-to-svg)"
    }

    try:
        response = httpx.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        result = response.json()
    except httpx.HTTPError as error:
        raise httpx.HTTPError(
            f"Failed to get polygon for OSM object '{osm_id}': {error}"
        ) from error

    geometry = result.get("geometry") if isinstance(result, dict) else None
    if not isinstance(geometry, dict) or geometry.get("type") != "Polygon":
        raise ValueError(
            f"OSM object '{osm_id}' does not have a supported polygon geometry"
        )

    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) != 1:
        raise ValueError(
            f"OSM object '{osm_id}' has holes or an unsupported polygon geometry"
        )
    ring = coordinates[0]
    if not isinstance(ring, list):
        raise TypeError(f"OSM object '{osm_id}' has invalid polygon coordinates")

    try:
        polygon = tuple(
            (float(latitude), float(longitude)) for longitude, latitude in ring
        )
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"OSM object '{osm_id}' has invalid polygon coordinates"
        ) from error

    try:
        return validate_bbox(polygon)
    except ValueError as error:
        raise ValueError(
            f"OSM object '{osm_id}' has invalid polygon geometry: {error}"
        ) from error
