"""Utilities for computing a bounding box around a geographic coordinate."""

import math

from osm_to_svg.validation import validate_bbox


def _validate_positive_distance(name: str, value: float | None) -> None:
    """Raise ValueError if value is not None and not strictly positive."""
    if value is not None and value <= 0:
        raise ValueError(f"{name} must be greater than 0")


def _kilometers_per_longitude_degree(latitude: float) -> float:
    """Return the ground distance in km represented by one degree of longitude at the given latitude."""
    km = 111.0 * math.cos(math.radians(latitude))
    if abs(km) < 1e-9:
        raise ValueError(
            "Cannot build east/west bounding box at this latitude because "
            "longitude degrees approach zero length near the poles."
        )
    return km


def get_bbox_around_coordinates(
    lat: float,
    lon: float,
    *,
    width_km: float | None = None,
    east_km: float | None = None,
    west_km: float | None = None,
    height_km: float | None = None,
    north_km: float | None = None,
    south_km: float | None = None,
) -> tuple[float, float, float, float]:
    """Compute a bounding box of the requested size centred on the given coordinates.

    Exactly one horizontal sizing method must be supplied: either ``width_km``
    (symmetric) or both ``east_km`` **and** ``west_km`` (asymmetric). The same
    rule applies vertically: either ``height_km`` or both ``north_km`` and
    ``south_km``.

    Args:
        lat: Centre latitude in decimal degrees.
        lon: Centre longitude in decimal degrees.
        width_km: Total east–west extent of the bounding box in kilometres
            (splits evenly around the centre).
        east_km: Distance east of the centre in kilometres.
        west_km: Distance west of the centre in kilometres.
        height_km: Total north–south extent of the bounding box in kilometres
            (splits evenly around the centre).
        north_km: Distance north of the centre in kilometres.
        south_km: Distance south of the centre in kilometres.

    Returns:
        Bounding box as ``(min_lon, min_lat, max_lon, max_lat)``.

    Raises:
        ValueError: If conflicting or incomplete sizing arguments are given, or
            if the resulting coordinates are invalid (e.g. coordinates at the
            poles where longitude degrees have zero length).
    """
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

    lat_degree_km = 111.0
    lon_degree_km = _kilometers_per_longitude_degree(lat)

    north_offset = north_km / lat_degree_km
    south_offset = south_km / lat_degree_km
    east_offset = east_km / lon_degree_km
    west_offset = west_km / lon_degree_km

    min_lat = lat - south_offset
    max_lat = lat + north_offset
    min_lon = lon - west_offset
    max_lon = lon + east_offset

    return validate_bbox((min_lon, min_lat, max_lon, max_lat))
