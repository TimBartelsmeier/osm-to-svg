"""OSM to SVG - A Python library for creating SVG files from OpenStreetMap data."""

from osm_to_svg import features
from osm_to_svg.downloader import download_from_overpass, download_from_url
from osm_to_svg.extractor import extract_from_pbf
from osm_to_svg.features import FeatureSpec
from osm_to_svg.geocoding import get_bbox_from_place
from osm_to_svg.models import Style
from osm_to_svg.SvgMapper import SvgMapper

__version__ = "0.1.0"

__all__ = [
    # Core classes
    "SvgMapper",
    "Style",
    # Feature API
    "features",
    "FeatureSpec",
    # Download/extract functions
    "download_from_overpass",
    "download_from_url",
    "extract_from_pbf",
    "get_bbox_from_place",
]
