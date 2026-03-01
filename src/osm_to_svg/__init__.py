"""OSM to SVG - A Python library for creating SVG files from OpenStreetMap data."""

from osm_to_svg.downloader import download_from_overpass, download_from_url
from osm_to_svg.extractor import extract_from_pbf
from osm_to_svg.features import (
    ACTIVE_RAILWAYS,
    AGRICULTURAL_LAND,
    ALL_GREEN_SPACES,
    ARTERIAL_ROADS,
    ARTIFICIAL_WATERWAYS,
    COMMERCIAL_BUILDINGS,
    FORESTS,
    INACTIVE_RAILWAYS,
    INDUSTRIAL_BUILDINGS,
    INSTITUTIONAL_BUILDINGS,
    LINEAR_WATERWAYS,
    LOCAL_ROADS,
    MAJOR_ROADS,
    MAJOR_WATERWAYS,
    MULTI_FAMILY_HOMES,
    NATURAL_VEGETATION,
    NATURAL_WATERWAYS,
    PARKS_AND_GARDENS,
    PEDESTRIAN_PATHS,
    PROTECTED_AREAS,
    RELIGIOUS_BUILDINGS,
    RESIDENTIAL_BUILDINGS,
    SINGLE_FAMILY_HOMES,
    URBAN_TRANSIT,
    WATER_BODIES,
    BuildingType,
    GreenSpaceType,
    RailwayType,
    RoadType,
    WaterwayType,
)
from osm_to_svg.geocoding import get_bbox_from_place
from osm_to_svg.models import Style
from osm_to_svg.SvgMapper import SvgMapper

__version__ = "0.1.0"

__all__ = [
    # Core classes
    "SvgMapper",
    "Style",
    # Download/extract functions
    "download_from_overpass",
    "download_from_url",
    "extract_from_pbf",
    "get_bbox_from_place",
    # Feature type enums
    "RoadType",
    "RailwayType",
    "WaterwayType",
    "BuildingType",
    "GreenSpaceType",
    # Road shorthands
    "MAJOR_ROADS",
    "ARTERIAL_ROADS",
    "LOCAL_ROADS",
    "PEDESTRIAN_PATHS",
    # Railway shorthands
    "ACTIVE_RAILWAYS",
    "URBAN_TRANSIT",
    "INACTIVE_RAILWAYS",
    # Waterway shorthands
    "LINEAR_WATERWAYS",
    "WATER_BODIES",
    "NATURAL_WATERWAYS",
    "ARTIFICIAL_WATERWAYS",
    "MAJOR_WATERWAYS",
    # Building shorthands
    "RESIDENTIAL_BUILDINGS",
    "COMMERCIAL_BUILDINGS",
    "INDUSTRIAL_BUILDINGS",
    "RELIGIOUS_BUILDINGS",
    "INSTITUTIONAL_BUILDINGS",
    "SINGLE_FAMILY_HOMES",
    "MULTI_FAMILY_HOMES",
    # Green space shorthands
    "PARKS_AND_GARDENS",
    "FORESTS",
    "NATURAL_VEGETATION",
    "PROTECTED_AREAS",
    "AGRICULTURAL_LAND",
    "ALL_GREEN_SPACES",
]
