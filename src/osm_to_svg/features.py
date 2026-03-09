"""OSM feature type definitions and tag mappings."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FeatureSpec:
    """Specifies which OSM features to extract, as a set of tag filters.

    tag_filters maps OSM tag keys to lists of accepted values (OR semantics).
    needs_areas enables multipolygon/area processing during PBF parsing, which
    is required for features that appear as closed areas (buildings, water bodies,
    green spaces) rather than plain ways.

    Specs can be combined with | to create a union that matches either.

    Example:
        >>> from osm_to_svg import features
        >>> spec = features.ROADS.MAJOR | features.WATERWAYS.BODIES
        >>> mapper.render_features(spec, style)
    """

    tag_filters: dict[str, list[str]] = field(default_factory=dict)
    needs_areas: bool = False

    def __or__(self, other: FeatureSpec) -> FeatureSpec:
        merged: dict[str, list[str]] = {}
        for key in set(self.tag_filters) | set(other.tag_filters):
            merged[key] = list(
                dict.fromkeys(
                    self.tag_filters.get(key, []) + other.tag_filters.get(key, [])
                )
            )
        return FeatureSpec(merged, self.needs_areas or other.needs_areas)


def _r(value: str) -> FeatureSpec:
    """Shorthand for a single highway= filter (roads)."""
    return FeatureSpec({"highway": [value]})


def _rw(value: str) -> FeatureSpec:
    """Shorthand for a single railway= filter."""
    return FeatureSpec({"railway": [value]})


def _w(value: str) -> FeatureSpec:
    """Shorthand for a single waterway= filter (linear waterways)."""
    return FeatureSpec({"waterway": [value]}, needs_areas=False)


def _wb(natural_value: str) -> FeatureSpec:
    """Shorthand for a water body via natural= tag (areas)."""
    return FeatureSpec({"natural": [natural_value]}, needs_areas=True)


def _b(value: str) -> FeatureSpec:
    """Shorthand for a single building= filter."""
    return FeatureSpec({"building": [value]}, needs_areas=True)


def _gs(tag_key: str, value: str) -> FeatureSpec:
    """Shorthand for a green space filter with an explicit tag key."""
    return FeatureSpec({tag_key: [value]}, needs_areas=True)


class ROADS:
    """Road features (OSM highway= tag).

    Individual types match a single highway= value.
    Shorthands group common subsets for cartographic use.

    Usage::

        from osm_to_svg import features
        mapper.render_features(features.ROADS.MAJOR, style)
        mapper.render_features(features.ROADS.MOTORWAY | features.ROADS.TRUNK, style)
    """

    # ---- individual types ----
    MOTORWAY = _r("motorway")
    MOTORWAY_LINK = _r("motorway_link")
    TRUNK = _r("trunk")
    TRUNK_LINK = _r("trunk_link")
    PRIMARY = _r("primary")
    PRIMARY_LINK = _r("primary_link")
    SECONDARY = _r("secondary")
    SECONDARY_LINK = _r("secondary_link")
    TERTIARY = _r("tertiary")
    TERTIARY_LINK = _r("tertiary_link")
    RESIDENTIAL = _r("residential")
    UNCLASSIFIED = _r("unclassified")
    SERVICE = _r("service")
    LIVING_STREET = _r("living_street")
    CYCLEWAY = _r("cycleway")
    FOOTWAY = _r("footway")
    PATH = _r("path")
    PEDESTRIAN_TYPE = _r("pedestrian")  # single highway=pedestrian value
    STEPS = _r("steps")
    TRACK = _r("track")
    ROAD = _r("road")

    # ---- shorthands ----
    # Major arterial roads (motorway through tertiary with all connecting links)
    # Use for: City/regional scale maps, main traffic network visualization
    MAJOR = FeatureSpec(
        {
            "highway": [
                "motorway",
                "motorway_link",
                "trunk",
                "trunk_link",
                "primary",
                "primary_link",
                "secondary",
                "secondary_link",
                "tertiary",
                "tertiary_link",
            ]
        }
    )
    # Highest hierarchy roads – main traffic arteries
    # Use for: Navigation-focused maps, highway system visualization
    ARTERIAL = FeatureSpec(
        {
            "highway": [
                "motorway",
                "motorway_link",
                "trunk",
                "trunk_link",
                "primary",
                "primary_link",
            ]
        }
    )
    # Local street network
    # Use for: Neighborhood maps, street-level detail
    LOCAL = FeatureSpec(
        {"highway": ["residential", "unclassified", "service", "living_street"]}
    )
    # Pedestrian-only paths and walkways (wins over PEDESTRIAN_TYPE)
    # Use for: Walkability maps, pedestrian navigation
    PEDESTRIAN = FeatureSpec({"highway": ["footway", "path", "pedestrian", "steps"]})


class RAILWAYS:
    """Railway features (OSM railway= tag).

    Usage::

        from osm_to_svg import features
        mapper.render_features(features.RAILWAYS.ACTIVE, style)
    """

    # ---- individual types ----
    RAIL = _rw("rail")
    LIGHT_RAIL = _rw("light_rail")
    SUBWAY = _rw("subway")
    TRAM = _rw("tram")
    MONORAIL = _rw("monorail")
    FUNICULAR = _rw("funicular")
    NARROW_GAUGE = _rw("narrow_gauge")
    ABANDONED = _rw("abandoned")
    DISUSED = _rw("disused")
    PRESERVED = _rw("preserved")

    # ---- shorthands ----
    # Currently operating railway infrastructure
    # Use for: Transit maps, active transportation network
    ACTIVE = FeatureSpec(
        {
            "railway": [
                "rail",
                "light_rail",
                "subway",
                "tram",
                "monorail",
                "funicular",
                "narrow_gauge",
            ]
        }
    )
    # Urban public transportation systems
    # Use for: City transit maps, public transport visualization
    URBAN_TRANSIT = FeatureSpec(
        {"railway": ["light_rail", "subway", "tram", "monorail"]}
    )
    # Defunct or historical railways
    # Use for: Heritage maps, historical infrastructure visualization
    INACTIVE = FeatureSpec({"railway": ["abandoned", "disused", "preserved"]})


class WATERWAYS:
    """Waterway and water body features.

    Linear waterways (RIVER, STREAM, …) use way geometry (needs_areas=False).
    Water bodies (WATER, LAKE, …) use area/polygon geometry (needs_areas=True).

    Note: LAKE, RESERVOIR, and POND all map to natural=water because OSM encodes
    the sub-type via a secondary ``water=`` tag that cannot be AND-filtered here.
    They are separate named specs for discoverability but are functionally equivalent.

    Usage::

        from osm_to_svg import features
        mapper.render_features(features.WATERWAYS.LINEAR | features.WATERWAYS.BODIES, style)
    """

    # ---- individual types ----
    RIVER = _w("river")
    STREAM = _w("stream")
    CANAL = _w("canal")
    DRAIN = _w("drain")
    DITCH = _w("ditch")
    WATER = _wb("water")
    LAKE = _wb("water")  # OSM: natural=water + water=lake (subtag not filterable here)
    RESERVOIR = _wb("water")  # OSM: natural=water + water=reservoir
    POND = _wb("water")  # OSM: natural=water + water=pond
    COASTLINE = _wb("coastline")

    # ---- shorthands ----
    # Flowing water features rendered as lines
    # Use for: Hydrography maps, drainage visualization
    LINEAR = FeatureSpec(
        {"waterway": ["river", "stream", "canal", "drain", "ditch"]},
        needs_areas=False,
    )
    # Standing water features rendered as polygons
    # Use for: Water body mapping, recreation area visualization
    BODIES = FeatureSpec({"natural": ["water"]}, needs_areas=True)
    # Natural watercourses and water bodies
    # Use for: Environmental maps, natural resource visualization
    NATURAL = FeatureSpec(
        {"waterway": ["river", "stream"], "natural": ["water"]},
        needs_areas=True,
    )
    # Human-constructed water infrastructure
    # Use for: Infrastructure maps, water management visualization
    ARTIFICIAL = FeatureSpec(
        {"waterway": ["canal", "drain", "ditch"], "natural": ["water"]},
        needs_areas=True,
    )
    # Major rivers and canals (navigable waterways)
    # Use for: Navigation maps, major hydrography features
    MAJOR = FeatureSpec(
        {"waterway": ["river", "canal"]},
        needs_areas=False,
    )


class BUILDINGS:
    """Building features (OSM building= tag).

    All building specs use area processing (needs_areas=True) because buildings
    are represented as closed polygons in OSM.

    Note: RESIDENTIAL_TYPE, COMMERCIAL_TYPE, and INDUSTRIAL_TYPE refer to the
    single OSM tag values ``building=residential``, ``building=commercial``, and
    ``building=industrial`` respectively. The shorthand names RESIDENTIAL,
    COMMERCIAL, and INDUSTRIAL cover broader groups of related building subtypes.

    Usage::

        from osm_to_svg import features
        mapper.render_features(features.BUILDINGS.RESIDENTIAL, style)
    """

    # ---- individual types ----
    YES = _b("yes")
    BUILDING = _b("building")
    HOUSE = _b("house")
    DETACHED = _b("detached")
    SEMIDETACHED_HOUSE = _b("semidetached_house")
    APARTMENTS = _b("apartments")
    TERRACE = _b("terrace")
    BUNGALOW = _b("bungalow")
    RESIDENTIAL_TYPE = _b("residential")  # single building=residential tag
    RETAIL = _b("retail")
    OFFICE = _b("office")
    SUPERMARKET = _b("supermarket")
    HOTEL = _b("hotel")
    COMMERCIAL_TYPE = _b("commercial")  # single building=commercial tag
    WAREHOUSE = _b("warehouse")
    MANUFACTURE = _b("manufacture")
    INDUSTRIAL_TYPE = _b("industrial")  # single building=industrial tag
    HOSPITAL = _b("hospital")
    SCHOOL = _b("school")
    UNIVERSITY = _b("university")
    CHURCH = _b("church")
    CATHEDRAL = _b("cathedral")
    MOSQUE = _b("mosque")
    TEMPLE = _b("temple")
    SYNAGOGUE = _b("synagogue")
    GOVERNMENT = _b("government")
    CIVIC = _b("civic")
    PUBLIC = _b("public")
    GARAGE = _b("garage")
    GARAGES = _b("garages")
    PARKING = _b("parking")
    SHED = _b("shed")
    ROOF = _b("roof")
    CONSTRUCTION = _b("construction")

    # ---- shorthands ----
    # All residential building types (housing stock)
    # Use for: Housing maps, residential density analysis
    RESIDENTIAL = FeatureSpec(
        {
            "building": [
                "residential",
                "house",
                "detached",
                "semidetached_house",
                "apartments",
                "terrace",
                "bungalow",
            ]
        },
        needs_areas=True,
    )
    # Commercial and business buildings
    # Use for: Business district maps, commercial activity visualization
    COMMERCIAL = FeatureSpec(
        {"building": ["commercial", "retail", "office", "supermarket", "hotel"]},
        needs_areas=True,
    )
    # Industrial facilities and warehouses
    # Use for: Industrial zone maps, logistics infrastructure
    INDUSTRIAL = FeatureSpec(
        {"building": ["industrial", "warehouse", "manufacture"]},
        needs_areas=True,
    )
    # Places of worship (all religions)
    # Use for: Cultural heritage maps, religious diversity visualization
    RELIGIOUS = FeatureSpec(
        {"building": ["church", "cathedral", "mosque", "temple", "synagogue"]},
        needs_areas=True,
    )
    # Public services and institutional buildings
    # Use for: Civic infrastructure maps, public services visualization
    INSTITUTIONAL = FeatureSpec(
        {
            "building": [
                "hospital",
                "school",
                "university",
                "government",
                "civic",
                "public",
            ]
        },
        needs_areas=True,
    )
    # Single-family residential structures
    # Use for: Low-density residential analysis
    SINGLE_FAMILY = FeatureSpec(
        {"building": ["house", "detached", "semidetached_house", "bungalow"]},
        needs_areas=True,
    )
    # Multi-family residential structures
    # Use for: Medium/high-density residential analysis
    MULTI_FAMILY = FeatureSpec(
        {"building": ["apartments", "terrace"]},
        needs_areas=True,
    )


class GREEN_SPACES:
    """Green space and vegetation features.

    Covers OSM leisure=, natural=, and landuse= tags.
    All green space specs use area processing (needs_areas=True).

    Usage::

        from osm_to_svg import features
        mapper.render_features(features.GREEN_SPACES.PARKS, style)
        mapper.render_features(features.GREEN_SPACES.FORESTS | features.GREEN_SPACES.PARKS, style)
    """

    # ---- individual types ----
    # leisure=
    PARK = _gs("leisure", "park")
    GARDEN = _gs("leisure", "garden")
    NATURE_RESERVE = _gs("leisure", "nature_reserve")
    RECREATION_GROUND = _gs("leisure", "recreation_ground")
    COMMON = _gs("leisure", "common")
    GOLF_COURSE = _gs("leisure", "golf_course")
    # natural=
    WOOD = _gs("natural", "wood")
    SCRUB = _gs("natural", "scrub")
    GRASSLAND = _gs("natural", "grassland")
    HEATH = _gs("natural", "heath")
    WETLAND = _gs("natural", "wetland")
    # landuse=
    FOREST = _gs("landuse", "forest")
    MEADOW = _gs("landuse", "meadow")
    GRASS = _gs("landuse", "grass")
    ORCHARD = _gs("landuse", "orchard")
    VINEYARD = _gs("landuse", "vineyard")
    CEMETERY = _gs("landuse", "cemetery")
    ALLOTMENTS = _gs("landuse", "allotments")

    # ---- shorthands ----
    # Public parks and gardens
    # Use for: Recreation maps, public amenity visualization
    PARKS = FeatureSpec(
        {"leisure": ["park", "garden", "recreation_ground", "common"]},
        needs_areas=True,
    )
    # Forested and wooded areas
    # Use for: Forest cover maps, vegetation analysis
    FORESTS = FeatureSpec(
        {"natural": ["wood"], "landuse": ["forest"]},
        needs_areas=True,
    )
    # Natural vegetation areas
    # Use for: Natural habitat maps, biodiversity visualization
    NATURAL = FeatureSpec(
        {"natural": ["wood", "scrub", "grassland", "heath", "wetland"]},
        needs_areas=True,
    )
    # Protected natural areas
    # Use for: Conservation maps, protected area visualization
    PROTECTED = FeatureSpec(
        {"leisure": ["nature_reserve"], "natural": ["wetland"]},
        needs_areas=True,
    )
    # Agricultural green spaces
    # Use for: Agricultural land use maps
    AGRICULTURAL = FeatureSpec(
        {"landuse": ["meadow", "grass", "orchard", "vineyard", "allotments"]},
        needs_areas=True,
    )
    # All green and natural spaces
    # Use for: Comprehensive green space analysis
    ALL = FeatureSpec(
        {
            "leisure": [
                "park",
                "garden",
                "nature_reserve",
                "recreation_ground",
                "common",
                "golf_course",
            ],
            "natural": ["wood", "scrub", "grassland", "heath", "wetland"],
            "landuse": [
                "forest",
                "meadow",
                "grass",
                "orchard",
                "vineyard",
                "cemetery",
                "allotments",
            ],
        },
        needs_areas=True,
    )
