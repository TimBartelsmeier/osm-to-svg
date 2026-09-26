"""OSM to SVG - A Python library for creating SVG files from OpenStreetMap data."""

from osm_to_svg import features
from osm_to_svg.acquisition import (
    download_from_overpass,
    download_from_url,
    extract_from_pbf,
    geocode_coordinates,
    geocode_osm_object,
    get_bbox_around_coordinates,
    get_polygon_from_osm_id,
)
from osm_to_svg.create_map import create_map
from osm_to_svg.features import FeatureSpec
from osm_to_svg.geojson import polygons_from_geojson
from osm_to_svg.mapper import SvgMapper
from osm_to_svg.models import (
    BoundingBox,
    FeatureFilter,
    FeatureLayer,
    OsmObjectId,
    PoiStyle,
    Polygon,
    Style,
)

__version__ = "0.1.0"

__all__ = [
    "BoundingBox",
    "FeatureFilter",
    "FeatureLayer",
    "FeatureSpec",
    "OsmObjectId",
    "PoiStyle",
    "Polygon",
    "Style",
    "SvgMapper",
    "create_map",
    "download_from_overpass",
    "download_from_url",
    "extract_from_pbf",
    "features",
    "geocode_coordinates",
    "geocode_osm_object",
    "get_bbox_around_coordinates",
    "get_polygon_from_osm_id",
    "polygons_from_geojson",
]
