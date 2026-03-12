"""OSM feature type definitions and tag mappings."""

from osm_to_svg.features.buildings import BUILDINGS
from osm_to_svg.features.green_spaces import GREEN_SPACES
from osm_to_svg.features.railways import RAILWAYS
from osm_to_svg.features.roads import ROADS
from osm_to_svg.features.spec import FeatureSpec
from osm_to_svg.features.water import WATER_POLYGONS, WATERWAYS

__all__ = [
    "FeatureSpec",
    "ROADS",
    "RAILWAYS",
    "WATERWAYS",
    "WATER_POLYGONS",
    "BUILDINGS",
    "GREEN_SPACES",
]
