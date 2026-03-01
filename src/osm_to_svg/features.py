"""OSM feature type definitions and tag mappings."""

from enum import Enum


class RoadType(str, Enum):
    """Road types based on OSM highway tag values."""

    # Major roads
    MOTORWAY = "motorway"
    MOTORWAY_LINK = "motorway_link"
    TRUNK = "trunk"
    TRUNK_LINK = "trunk_link"
    PRIMARY = "primary"
    PRIMARY_LINK = "primary_link"
    SECONDARY = "secondary"
    SECONDARY_LINK = "secondary_link"
    TERTIARY = "tertiary"
    TERTIARY_LINK = "tertiary_link"

    # Local roads
    RESIDENTIAL = "residential"
    UNCLASSIFIED = "unclassified"
    SERVICE = "service"
    LIVING_STREET = "living_street"

    # Pedestrian and cycle paths
    CYCLEWAY = "cycleway"
    FOOTWAY = "footway"
    PATH = "path"
    PEDESTRIAN = "pedestrian"
    STEPS = "steps"
    TRACK = "track"

    # Special
    ROAD = "road"  # Generic/unknown road type


class RailwayType(str, Enum):
    """Railway types based on OSM railway tag values."""

    RAIL = "rail"  # Standard gauge railway
    LIGHT_RAIL = "light_rail"  # Light rail / streetcar
    SUBWAY = "subway"  # Underground metro
    TRAM = "tram"  # Tram line
    MONORAIL = "monorail"
    FUNICULAR = "funicular"
    NARROW_GAUGE = "narrow_gauge"

    # Optional: inactive railways
    ABANDONED = "abandoned"
    DISUSED = "disused"
    PRESERVED = "preserved"  # Heritage railways


class WaterwayType(str, Enum):
    """Waterway types based on OSM waterway and natural tags."""

    # Linear waterways
    RIVER = "river"
    STREAM = "stream"
    CANAL = "canal"
    DRAIN = "drain"
    DITCH = "ditch"

    # Water bodies (from natural=water tag)
    WATER = "water"  # Generic water body
    LAKE = "lake"
    RESERVOIR = "reservoir"
    POND = "pond"

    # Coastline
    COASTLINE = "coastline"


class GreenSpaceType(str, Enum):
    """Green space types based on OSM leisure, natural, and landuse tags."""

    # Leisure areas
    PARK = "park"  # Public park
    GARDEN = "garden"  # Public garden
    NATURE_RESERVE = "nature_reserve"  # Protected nature reserve
    RECREATION_GROUND = "recreation_ground"  # Recreation area
    COMMON = "common"  # Common land
    GOLF_COURSE = "golf_course"  # Golf course

    # Natural vegetation
    WOOD = "wood"  # Forested area
    SCRUB = "scrub"  # Shrubland
    GRASSLAND = "grassland"  # Natural grassland
    HEATH = "heath"  # Heath/moorland
    WETLAND = "wetland"  # Wetland area

    # Land use
    FOREST = "forest"  # Managed forest
    MEADOW = "meadow"  # Meadow
    GRASS = "grass"  # Grass area
    ORCHARD = "orchard"  # Orchard
    VINEYARD = "vineyard"  # Vineyard
    CEMETERY = "cemetery"  # Cemetery
    ALLOTMENTS = "allotments"  # Allotment gardens


class BuildingType(str, Enum):
    """Building types based on OSM building tag values."""

    # Generic
    YES = "yes"  # Generic building
    BUILDING = "building"  # Same as 'yes'

    # Residential
    RESIDENTIAL = "residential"
    HOUSE = "house"
    DETACHED = "detached"
    SEMIDETACHED_HOUSE = "semidetached_house"
    APARTMENTS = "apartments"
    TERRACE = "terrace"
    BUNGALOW = "bungalow"

    # Commercial
    COMMERCIAL = "commercial"
    RETAIL = "retail"
    OFFICE = "office"
    SUPERMARKET = "supermarket"
    HOTEL = "hotel"

    # Industrial
    INDUSTRIAL = "industrial"
    WAREHOUSE = "warehouse"
    MANUFACTURE = "manufacture"

    # Public/Civic
    HOSPITAL = "hospital"
    SCHOOL = "school"
    UNIVERSITY = "university"
    CHURCH = "church"
    CATHEDRAL = "cathedral"
    MOSQUE = "mosque"
    TEMPLE = "temple"
    SYNAGOGUE = "synagogue"
    GOVERNMENT = "government"
    CIVIC = "civic"
    PUBLIC = "public"

    # Other
    GARAGE = "garage"
    GARAGES = "garages"
    PARKING = "parking"
    SHED = "shed"
    ROOF = "roof"
    CONSTRUCTION = "construction"


# Mapping from feature types to OSM tag keys
OSM_TAG_MAPPING = {
    RoadType: "highway",
    RailwayType: "railway",
    WaterwayType: None,  # Complex: waterway or natural=water
    BuildingType: "building",
    GreenSpaceType: None,  # Complex: leisure, natural, or landuse
}


def get_osm_filter(
    feature_type: type[Enum], subtypes: list[Enum] | None = None
) -> dict:
    """Get OSM tag filter for a feature type and optional subtypes.

    Args:
        feature_type: The feature type enum class (RoadType, RailwayType, etc.)
        subtypes: Optional list of specific subtypes to filter for

    Returns:
        Dictionary with tag key and list of values to match
    """
    if feature_type == WaterwayType:
        # Special handling for waterways (multiple possible tag keys)
        if subtypes:
            values = [st.value for st in subtypes]
            return {"waterway": values, "natural": ["water", "coastline"]}
        else:
            return {
                "waterway": ["river", "stream", "canal", "drain", "ditch"],
                "natural": ["water", "coastline"],
            }

    if feature_type == GreenSpaceType:
        # Special handling for green spaces (multiple possible tag keys)
        # Map each subtype to its appropriate OSM tag key
        leisure_types = [
            "park",
            "garden",
            "nature_reserve",
            "recreation_ground",
            "common",
            "golf_course",
        ]
        natural_types = ["wood", "scrub", "grassland", "heath", "wetland"]
        landuse_types = [
            "forest",
            "meadow",
            "grass",
            "orchard",
            "vineyard",
            "cemetery",
            "allotments",
        ]

        if subtypes:
            values = [st.value for st in subtypes]
            result = {}
            if any(v in leisure_types for v in values):
                result["leisure"] = [v for v in values if v in leisure_types]
            if any(v in natural_types for v in values):
                result["natural"] = [v for v in values if v in natural_types]
            if any(v in landuse_types for v in values):
                result["landuse"] = [v for v in values if v in landuse_types]
            return result
        else:
            return {
                "leisure": leisure_types,
                "natural": natural_types,
                "landuse": landuse_types,
            }

    tag_key = OSM_TAG_MAPPING.get(feature_type)
    if tag_key is None:
        raise ValueError(f"Unknown feature type: {feature_type}")

    if subtypes:
        values = [st.value for st in subtypes]
    else:
        # Get all possible values for this feature type
        values = [member.value for member in feature_type]

    return {tag_key: values}


# ============================================================================
# Shorthand Groupings for Common Use Cases
# ============================================================================
# These constants provide convenient groupings of feature subtypes for
# common cartographic tasks. Use them with render_features() to avoid
# manually listing subtypes.


# Road Type Shorthands
# ============================================================================

# Major arterial roads (motorway through tertiary with all connecting links)
# Use for: City/regional scale maps, main traffic network visualization
MAJOR_ROADS = [
    RoadType.MOTORWAY,
    RoadType.MOTORWAY_LINK,
    RoadType.TRUNK,
    RoadType.TRUNK_LINK,
    RoadType.PRIMARY,
    RoadType.PRIMARY_LINK,
    RoadType.SECONDARY,
    RoadType.SECONDARY_LINK,
    RoadType.TERTIARY,
    RoadType.TERTIARY_LINK,
]

# Highest hierarchy roads (motorway, trunk, primary) - main traffic arteries
# Use for: Navigation-focused maps, highway system visualization
ARTERIAL_ROADS = [
    RoadType.MOTORWAY,
    RoadType.MOTORWAY_LINK,
    RoadType.TRUNK,
    RoadType.TRUNK_LINK,
    RoadType.PRIMARY,
    RoadType.PRIMARY_LINK,
]

# Local street network (residential and service roads)
# Use for: Neighborhood maps, street-level detail
LOCAL_ROADS = [
    RoadType.RESIDENTIAL,
    RoadType.UNCLASSIFIED,
    RoadType.SERVICE,
    RoadType.LIVING_STREET,
]

# Pedestrian-only paths and walkways
# Use for: Walkability maps, pedestrian navigation
PEDESTRIAN_PATHS = [
    RoadType.FOOTWAY,
    RoadType.PATH,
    RoadType.PEDESTRIAN,
    RoadType.STEPS,
]


# Railway Type Shorthands
# ============================================================================

# Currently operating railway infrastructure
# Use for: Transit maps, active transportation network
ACTIVE_RAILWAYS = [
    RailwayType.RAIL,
    RailwayType.LIGHT_RAIL,
    RailwayType.SUBWAY,
    RailwayType.TRAM,
    RailwayType.MONORAIL,
    RailwayType.FUNICULAR,
    RailwayType.NARROW_GAUGE,
]

# Urban public transportation systems
# Use for: City transit maps, public transport visualization
URBAN_TRANSIT = [
    RailwayType.LIGHT_RAIL,
    RailwayType.SUBWAY,
    RailwayType.TRAM,
    RailwayType.MONORAIL,
]

# Defunct or historical railways
# Use for: Heritage maps, historical infrastructure visualization
INACTIVE_RAILWAYS = [
    RailwayType.ABANDONED,
    RailwayType.DISUSED,
    RailwayType.PRESERVED,
]


# Waterway Type Shorthands
# ============================================================================

# Flowing water features rendered as lines
# Use for: Hydrography maps, drainage visualization
LINEAR_WATERWAYS = [
    WaterwayType.RIVER,
    WaterwayType.STREAM,
    WaterwayType.CANAL,
    WaterwayType.DRAIN,
    WaterwayType.DITCH,
]

# Standing water features rendered as polygons
# Use for: Water body mapping, recreation area visualization
WATER_BODIES = [
    WaterwayType.WATER,
    WaterwayType.LAKE,
    WaterwayType.RESERVOIR,
    WaterwayType.POND,
]

# Natural watercourses and water bodies
# Use for: Environmental maps, natural resource visualization
NATURAL_WATERWAYS = [
    WaterwayType.RIVER,
    WaterwayType.STREAM,
    WaterwayType.LAKE,
    WaterwayType.POND,
]

# Human-constructed water infrastructure
# Use for: Infrastructure maps, water management visualization
ARTIFICIAL_WATERWAYS = [
    WaterwayType.CANAL,
    WaterwayType.DRAIN,
    WaterwayType.DITCH,
    WaterwayType.RESERVOIR,
]

# Major rivers and canals (navigable waterways)
# Use for: Navigation maps, major hydrography features
MAJOR_WATERWAYS = [
    WaterwayType.RIVER,
    WaterwayType.CANAL,
]


# Building Type Shorthands
# ============================================================================

# All residential building types (housing stock)
# Use for: Housing maps, residential density analysis
RESIDENTIAL_BUILDINGS = [
    BuildingType.RESIDENTIAL,
    BuildingType.HOUSE,
    BuildingType.DETACHED,
    BuildingType.SEMIDETACHED_HOUSE,
    BuildingType.APARTMENTS,
    BuildingType.TERRACE,
    BuildingType.BUNGALOW,
]

# Commercial and business buildings
# Use for: Business district maps, commercial activity visualization
COMMERCIAL_BUILDINGS = [
    BuildingType.COMMERCIAL,
    BuildingType.RETAIL,
    BuildingType.OFFICE,
    BuildingType.SUPERMARKET,
    BuildingType.HOTEL,
]

# Industrial facilities and warehouses
# Use for: Industrial zone maps, logistics infrastructure
INDUSTRIAL_BUILDINGS = [
    BuildingType.INDUSTRIAL,
    BuildingType.WAREHOUSE,
    BuildingType.MANUFACTURE,
]

# Places of worship (all religions)
# Use for: Cultural heritage maps, religious diversity visualization
RELIGIOUS_BUILDINGS = [
    BuildingType.CHURCH,
    BuildingType.CATHEDRAL,
    BuildingType.MOSQUE,
    BuildingType.TEMPLE,
    BuildingType.SYNAGOGUE,
]

# Public services and institutional buildings
# Use for: Civic infrastructure maps, public services visualization
INSTITUTIONAL_BUILDINGS = [
    BuildingType.HOSPITAL,
    BuildingType.SCHOOL,
    BuildingType.UNIVERSITY,
    BuildingType.GOVERNMENT,
    BuildingType.CIVIC,
    BuildingType.PUBLIC,
]

# Single-family residential structures
# Use for: Low-density residential analysis
SINGLE_FAMILY_HOMES = [
    BuildingType.HOUSE,
    BuildingType.DETACHED,
    BuildingType.SEMIDETACHED_HOUSE,
    BuildingType.BUNGALOW,
]

# Multi-family residential structures
# Use for: Medium/high-density residential analysis
MULTI_FAMILY_HOMES = [
    BuildingType.APARTMENTS,
    BuildingType.TERRACE,
]


# Green Space Type Shorthands
# ============================================================================

# Public parks and gardens
# Use for: Recreation maps, public amenity visualization
PARKS_AND_GARDENS = [
    GreenSpaceType.PARK,
    GreenSpaceType.GARDEN,
    GreenSpaceType.RECREATION_GROUND,
    GreenSpaceType.COMMON,
]

# Forested and wooded areas
# Use for: Forest cover maps, vegetation analysis
FORESTS = [
    GreenSpaceType.WOOD,
    GreenSpaceType.FOREST,
]

# Natural vegetation areas
# Use for: Natural habitat maps, biodiversity visualization
NATURAL_VEGETATION = [
    GreenSpaceType.WOOD,
    GreenSpaceType.SCRUB,
    GreenSpaceType.GRASSLAND,
    GreenSpaceType.HEATH,
    GreenSpaceType.WETLAND,
]

# Protected natural areas
# Use for: Conservation maps, protected area visualization
PROTECTED_AREAS = [
    GreenSpaceType.NATURE_RESERVE,
    GreenSpaceType.WETLAND,
]

# Agricultural green spaces
# Use for: Agricultural land use maps
AGRICULTURAL_LAND = [
    GreenSpaceType.MEADOW,
    GreenSpaceType.GRASS,
    GreenSpaceType.ORCHARD,
    GreenSpaceType.VINEYARD,
    GreenSpaceType.ALLOTMENTS,
]

# All green and natural spaces
# Use for: Comprehensive green space analysis
ALL_GREEN_SPACES = [
    GreenSpaceType.PARK,
    GreenSpaceType.GARDEN,
    GreenSpaceType.NATURE_RESERVE,
    GreenSpaceType.RECREATION_GROUND,
    GreenSpaceType.COMMON,
    GreenSpaceType.WOOD,
    GreenSpaceType.SCRUB,
    GreenSpaceType.GRASSLAND,
    GreenSpaceType.HEATH,
    GreenSpaceType.WETLAND,
    GreenSpaceType.FOREST,
    GreenSpaceType.MEADOW,
    GreenSpaceType.GRASS,
]
