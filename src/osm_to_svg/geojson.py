"""Utilities for converting GeoJSON polygon data to library polygons."""

import json
from collections.abc import Mapping
from typing import Any

from osm_to_svg.models import Polygon
from osm_to_svg.validation import validate_bbox


def polygons_from_json(
    geojson: Mapping[str, Any] | str | bytes,
) -> list[Polygon]:
    """Convert GeoJSON polygons into the library's ``Polygon`` type.

    The input may be a GeoJSON ``Polygon``, ``Feature`` containing a Polygon,
    or a ``FeatureCollection`` containing one or more such Features. The
    result always contains one or more Polygons. GeoJSON coordinates are
    converted from ``(longitude, latitude)`` to the library's ``(latitude,
    longitude)`` order.

    Args:
        geojson: Parsed GeoJSON data or a JSON string/bytes value.

    Returns:
        A list of validated, closed Polygons.

    Raises:
        TypeError: If the input or polygon coordinates have an invalid type.
        ValueError: If the input is not a supported polygon, has holes, or
            contains invalid polygon geometry.
    """
    document = _parse_geojson(geojson)
    geometries = _get_geometries(document)
    return [_polygon_from_geometry(geometry) for geometry in geometries]


def _polygon_from_geometry(geometry: Mapping[str, Any]) -> Polygon:

    if geometry.get("type") != "Polygon":
        raise ValueError("GeoJSON does not have a supported polygon geometry")

    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) != 1:
        raise ValueError("GeoJSON polygons with holes are not supported")

    ring = coordinates[0]
    if not isinstance(ring, list):
        raise TypeError("invalid polygon coordinates")

    try:
        polygon = tuple(
            (float(latitude), float(longitude)) for longitude, latitude in ring
        )
    except (TypeError, ValueError) as error:
        raise ValueError("invalid polygon coordinates") from error

    try:
        return validate_bbox(polygon)
    except ValueError as error:
        raise ValueError(f"invalid polygon geometry: {error}") from error


def _parse_geojson(geojson: Mapping[str, Any] | str | bytes) -> Mapping[str, Any]:
    if isinstance(geojson, (str, bytes)):
        try:
            parsed = json.loads(geojson)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError("invalid GeoJSON document") from error
    else:
        parsed = geojson

    if not isinstance(parsed, Mapping):
        raise TypeError("GeoJSON must be a mapping, JSON string, or JSON bytes")
    return parsed


def _get_geometries(document: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    document_type = document.get("type")
    if document_type == "Feature":
        geometries = [document.get("geometry")]
    elif document_type == "FeatureCollection":
        features = document.get("features")
        if not isinstance(features, list) or not features:
            raise ValueError(
                "GeoJSON FeatureCollection must contain at least one Feature"
            )
        geometries = [
            feature.get("geometry") if isinstance(feature, Mapping) else None
            for feature in features
        ]
    elif document_type == "Polygon":
        geometries = [document]
    else:
        raise ValueError("GeoJSON does not have a supported polygon geometry")

    valid_geometries: list[Mapping[str, Any]] = []
    for geometry in geometries:
        if not isinstance(geometry, Mapping):
            raise TypeError("GeoJSON Feature has no valid geometry")
        valid_geometries.append(geometry)
    return tuple(valid_geometries)
