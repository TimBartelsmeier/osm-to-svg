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
        >>> spec = features.ROADS.MAJOR | features.WATER.BODIES
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
    """highway=motorway: High-capacity divided motorway; access via entry/exit ramps only."""
    MOTORWAY_LINK = _r("motorway_link")
    """highway=motorway_link: Ramp connecting to or from a motorway."""
    TRUNK = _r("trunk")
    """highway=trunk: High-importance road that does not meet full motorway standard."""
    TRUNK_LINK = _r("trunk_link")
    """highway=trunk_link: Ramp connecting to or from a trunk road."""
    PRIMARY = _r("primary")
    """highway=primary: Major road linking large towns."""
    PRIMARY_LINK = _r("primary_link")
    """highway=primary_link: Slip road connecting to a primary road."""
    SECONDARY = _r("secondary")
    """highway=secondary: Road linking towns and larger villages."""
    SECONDARY_LINK = _r("secondary_link")
    """highway=secondary_link: Slip road connecting to a secondary road."""
    TERTIARY = _r("tertiary")
    """highway=tertiary: Road linking smaller settlements."""
    TERTIARY_LINK = _r("tertiary_link")
    """highway=tertiary_link: Slip road connecting to a tertiary road."""
    RESIDENTIAL = _r("residential")
    """highway=residential: Road within a residential area."""
    UNCLASSIFIED = _r("unclassified")
    """highway=unclassified: Minor road connecting settlements; lowest public road class."""
    SERVICE = _r("service")
    """highway=service: Access road for parking lots, driveways, and service areas."""
    LIVING_STREET = _r("living_street")
    """highway=living_street: Pedestrian-priority street with very low speed limit."""
    CYCLEWAY = _r("cycleway")
    """highway=cycleway: Dedicated cycling path."""
    FOOTWAY = _r("footway")
    """highway=footway: Designated footpath for pedestrians."""
    PATH = _r("path")
    """highway=path: Unpaved trail shared by pedestrians, cyclists, or horses."""
    PEDESTRIAN_TYPE = _r("pedestrian")  # single highway=pedestrian value
    """highway=pedestrian: Pedestrianised street or plaza (single tag value; see PEDESTRIAN for the group shorthand)."""
    STEPS = _r("steps")
    """highway=steps: Stairway connection between levels."""
    TRACK = _r("track")
    """highway=track: Unpaved track for agricultural or forestry access."""
    ROAD = _r("road")
    """highway=road: Road of unknown or unspecified classification."""

    # ---- shorthands ----
    MAJOR = (
        MOTORWAY
        | MOTORWAY_LINK
        | TRUNK
        | TRUNK_LINK
        | PRIMARY
        | PRIMARY_LINK
        | SECONDARY
        | SECONDARY_LINK
        | TERTIARY
        | TERTIARY_LINK
    )
    """Shorthand for arterial road network from motorway through tertiary, including link roads.

    OSM tags: highway=motorway, motorway_link, trunk, trunk_link, primary,
    primary_link, secondary, secondary_link, tertiary, tertiary_link.
    """
    ARTERIAL = MOTORWAY | MOTORWAY_LINK | TRUNK | TRUNK_LINK | PRIMARY | PRIMARY_LINK
    """Shorthand for highest-hierarchy roads: motorway, trunk, and primary classes with links.

    OSM tags: highway=motorway, motorway_link, trunk, trunk_link, primary,
    primary_link.
    """
    LOCAL = RESIDENTIAL | UNCLASSIFIED | SERVICE | LIVING_STREET
    """Shorthand for local access street network and traffic-calmed residential streets.

    OSM tags: highway=residential, unclassified, service, living_street.
    """
    PEDESTRIAN = FOOTWAY | PATH | PEDESTRIAN_TYPE | STEPS
    """Shorthand for pedestrian-focused paths, walkways, and stair connections.

    OSM tags: highway=footway, path, pedestrian, steps.
    
    See also PEDESTRIAN_TYPE for the single highway=pedestrian tag value.
    """


class RAILWAYS:
    """Railway features (OSM railway= tag).

    Usage::

        from osm_to_svg import features
        mapper.render_features(features.RAILWAYS.ACTIVE, style)
    """

    # ---- individual types ----
    RAIL = _rw("rail")
    """railway=rail: Standard-gauge heavy rail lines."""
    LIGHT_RAIL = _rw("light_rail")
    """railway=light_rail: Light rail and commuter rail lines."""
    SUBWAY = _rw("subway")
    """railway=subway: Underground metro/subway lines."""
    TRAM = _rw("tram")
    """railway=tram: Street-running tram lines."""
    MONORAIL = _rw("monorail")
    """railway=monorail: Single-rail guided transit lines."""
    FUNICULAR = _rw("funicular")
    """railway=funicular: Cable-driven steep hillside railway."""
    NARROW_GAUGE = _rw("narrow_gauge")
    """railway=narrow_gauge: Railway with narrower-than-standard track gauge."""
    ABANDONED = _rw("abandoned")
    """railway=abandoned: Line that has been abandoned; track may still be physically present."""
    DISUSED = _rw("disused")
    """railway=disused: Line no longer in service but infrastructure is still intact."""
    PRESERVED = _rw("preserved")
    """railway=preserved: Heritage or museum railway kept for historical purposes."""

    # ---- shorthands ----
    ACTIVE = RAIL | LIGHT_RAIL | SUBWAY | TRAM | MONORAIL | FUNICULAR | NARROW_GAUGE
    """Shorthand for currently operating railway and rail-transit infrastructure.

    OSM tags: railway=rail, light_rail, subway, tram, monorail, funicular,
    narrow_gauge.
    """
    URBAN_TRANSIT = LIGHT_RAIL | SUBWAY | TRAM | MONORAIL
    """Shorthand for urban rail transit systems.

    OSM tags: railway=light_rail, subway, tram, monorail.
    """
    INACTIVE = ABANDONED | DISUSED | PRESERVED
    """Shorthand for non-operational and heritage railway lines.

    OSM tags: railway=abandoned, disused, preserved.
    """


class WATER:
    """Waterway and water body features.

    Linear waterways (RIVER, STREAM, …) use way geometry (needs_areas=False).
    Water bodies (WATER_AREA, LAKE, …) use area/polygon geometry (needs_areas=True).

    Note: LAKE, RESERVOIR, and POND all map to natural=water because OSM encodes
    the sub-type via a secondary ``water=`` tag that cannot be AND-filtered here.
    They are separate named specs for discoverability but are functionally equivalent.

    Usage::

        from osm_to_svg import features
        mapper.render_features(features.WATER.LINEAR | features.WATER.BODIES, style)
    """

    # ---- individual types ----
    RIVER = _w("river")
    """waterway=river: Major natural watercourse."""
    STREAM = _w("stream")
    """waterway=stream: Minor natural watercourse, smaller than a river."""
    CANAL = _w("canal")
    """waterway=canal: Artificial navigable waterway."""
    DRAIN = _w("drain")
    """waterway=drain: Artificial drainage channel, typically not navigable."""
    DITCH = _w("ditch")
    """waterway=ditch: Small artificial drainage ditch."""
    WATER_AREA = _wb(
        "water"
    )  # OSM: natural=water + water=lake (subtag not filterable here)
    """natural=water: Generic standing water area. The water= sub-type (lake, pond, reservoir) is not filterable here."""
    LAKE = _wb("water")  # OSM: natural=water + water=lake (subtag not filterable here)
    """natural=water (+ water=lake): Lake; the water= sub-type is not filterable here — equivalent to WATER_AREA."""
    RESERVOIR = _wb("water")  # OSM: natural=water + water=reservoir
    """natural=water (+ water=reservoir): Artificial water reservoir; the water= sub-type is not filterable here — equivalent to WATER_AREA."""
    POND = _wb("water")  # OSM: natural=water + water=pond
    """natural=water (+ water=pond): Small pond; the water= sub-type is not filterable here — equivalent to WATER_AREA."""
    COASTLINE = _wb("coastline")
    """natural=coastline: Ocean/sea coastline boundary rendered as an area."""

    # ---- shorthands ----
    LINEAR = RIVER | STREAM | CANAL | DRAIN | DITCH
    """Shorthand for flowing and channelized waterways rendered as line features.

    OSM tags: waterway=river, stream, canal, drain, ditch.
    """
    BODIES = WATER_AREA
    """Shorthand for standing inland water areas represented as polygons.

    OSM tags: natural=water.
    """
    NATURAL = RIVER | STREAM | WATER_AREA
    """Shorthand for natural watercourses and standing natural water areas.

    OSM tags: waterway=river, stream; natural=water.
    """
    ARTIFICIAL = CANAL | DRAIN | DITCH | WATER_AREA
    """Shorthand for human-made channels together with standing water areas.

    OSM tags: waterway=canal, drain, ditch; natural=water.
    """
    MAJOR = RIVER | CANAL
    """Shorthand for major navigable waterways rendered as line features.

    OSM tags: waterway=river, canal.
    """


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
    """building=yes: Unspecified building (generic building outline with no further classification)."""
    BUILDING = _b("building")
    """building=building: Explicitly tagged as building=building (rare OSM usage)."""
    HOUSE = _b("house")
    """building=house: Single-family detached house."""
    DETACHED = _b("detached")
    """building=detached: Fully detached residential building, standing alone on its plot."""
    SEMIDETACHED_HOUSE = _b("semidetached_house")
    """building=semidetached_house: Two residential units sharing one party wall."""
    APARTMENTS = _b("apartments")
    """building=apartments: Multi-unit apartment building."""
    TERRACE = _b("terrace")
    """building=terrace: Row of terraced houses sharing party walls."""
    BUNGALOW = _b("bungalow")
    """building=bungalow: Single-storey house."""
    RESIDENTIAL_TYPE = _b("residential")  # single building=residential tag
    """building=residential: Generic residential building (single tag value; see RESIDENTIAL for the group shorthand)."""
    RETAIL = _b("retail")
    """building=retail: Building used for retail trade."""
    OFFICE = _b("office")
    """building=office: Office building."""
    SUPERMARKET = _b("supermarket")
    """building=supermarket: Supermarket building."""
    HOTEL = _b("hotel")
    """building=hotel: Hotel building."""
    COMMERCIAL_TYPE = _b("commercial")  # single building=commercial tag
    """building=commercial: Generic commercial building (single tag value; see COMMERCIAL for the group shorthand)."""
    WAREHOUSE = _b("warehouse")
    """building=warehouse: Large storage building."""
    MANUFACTURE = _b("manufacture")
    """building=manufacture: Manufacturing or factory building."""
    INDUSTRIAL_TYPE = _b("industrial")  # single building=industrial tag
    """building=industrial: Generic industrial building (single tag value; see INDUSTRIAL for the group shorthand)."""
    HOSPITAL = _b("hospital")
    """building=hospital: Hospital or medical facility building."""
    SCHOOL = _b("school")
    """building=school: School building."""
    UNIVERSITY = _b("university")
    """building=university: University building."""
    CHURCH = _b("church")
    """building=church: Christian church building."""
    CATHEDRAL = _b("cathedral")
    """building=cathedral: Cathedral building."""
    MOSQUE = _b("mosque")
    """building=mosque: Mosque building."""
    TEMPLE = _b("temple")
    """building=temple: Temple building."""
    SYNAGOGUE = _b("synagogue")
    """building=synagogue: Synagogue building."""
    GOVERNMENT = _b("government")
    """building=government: Government or public administration building."""
    CIVIC = _b("civic")
    """building=civic: Civic building for public services."""
    PUBLIC = _b("public")
    """building=public: Generic public-use building."""
    GARAGE = _b("garage")
    """building=garage: Single private garage."""
    GARAGES = _b("garages")
    """building=garages: Block of multiple private garages."""
    PARKING = _b("parking")
    """building=parking: Multi-storey or enclosed parking structure."""
    SHED = _b("shed")
    """building=shed: Small outbuilding or storage shed."""
    ROOF = _b("roof")
    """building=roof: Roof structure with no fully enclosed walls."""
    CONSTRUCTION = _b("construction")
    """building=construction: Building currently under construction."""

    # ---- shorthands ----
    RESIDENTIAL = (
        RESIDENTIAL_TYPE
        | HOUSE
        | DETACHED
        | SEMIDETACHED_HOUSE
        | APARTMENTS
        | TERRACE
        | BUNGALOW
    )
    """Shorthand for residential dwelling buildings across detached, attached, and multi-unit forms.

    OSM tags: building=residential, house, detached, semidetached_house,
    apartments, terrace, bungalow.

    See also RESIDENTIAL_TYPE for the single tag value.
    """
    COMMERCIAL = COMMERCIAL_TYPE | RETAIL | OFFICE | SUPERMARKET | HOTEL
    """Shorthand for commercial and business-use buildings.

    OSM tags: building=commercial, retail, office, supermarket, hotel.

    See also COMMERCIAL_TYPE for the single tag value.
    """
    INDUSTRIAL = INDUSTRIAL_TYPE | WAREHOUSE | MANUFACTURE
    """Shorthand for industrial production and storage buildings.

    OSM tags: building=industrial, warehouse, manufacture.

    See also INDUSTRIAL_TYPE for the single tag value.
    """
    RELIGIOUS = CHURCH | CATHEDRAL | MOSQUE | TEMPLE | SYNAGOGUE
    """Shorthand for places of worship and religious buildings.

    OSM tags: building=church, cathedral, mosque, temple, synagogue.
    """
    INSTITUTIONAL = HOSPITAL | SCHOOL | UNIVERSITY | GOVERNMENT | CIVIC | PUBLIC
    """Shorthand for civic, government, education, and healthcare institutions.

    OSM tags: building=hospital, school, university, government, civic, public.
    """
    SINGLE_FAMILY = HOUSE | DETACHED | SEMIDETACHED_HOUSE | BUNGALOW
    """Shorthand for single-household and low-density dwelling buildings.

    OSM tags: building=house, detached, semidetached_house, bungalow.
    """
    MULTI_FAMILY = APARTMENTS | TERRACE
    """Shorthand for multi-household residential buildings.

    OSM tags: building=apartments, terrace.
    """


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
    """leisure=park: Public park."""
    GARDEN = _gs("leisure", "garden")
    """leisure=garden: Public or private garden."""
    NATURE_RESERVE = _gs("leisure", "nature_reserve")
    """leisure=nature_reserve: Protected nature reserve."""
    RECREATION_GROUND = _gs("leisure", "recreation_ground")
    """leisure=recreation_ground: Open area set aside for outdoor recreation."""
    COMMON = _gs("leisure", "common")
    """leisure=common: Public common land available for general use."""
    GOLF_COURSE = _gs("leisure", "golf_course")
    """leisure=golf_course: Golf course."""
    # natural=
    WOOD = _gs("natural", "wood")
    """natural=wood: Naturally occurring woodland or forest."""
    SCRUB = _gs("natural", "scrub")
    """natural=scrub: Shrubland and scrubby vegetation."""
    GRASSLAND = _gs("natural", "grassland")
    """natural=grassland: Natural grassy area."""
    HEATH = _gs("natural", "heath")
    """natural=heath: Heath or moorland."""
    WETLAND = _gs("natural", "wetland")
    """natural=wetland: Wetland or marsh area."""
    # landuse=
    FOREST = _gs("landuse", "forest")
    """landuse=forest: Managed forest or woodland (may overlap with natural=wood)."""
    MEADOW = _gs("landuse", "meadow")
    """landuse=meadow: Meadow used for mowing or grazing."""
    GRASS = _gs("landuse", "grass")
    """landuse=grass: Managed grassed area such as a park lawn or road verge."""
    ORCHARD = _gs("landuse", "orchard")
    """landuse=orchard: Fruit or nut tree plantation."""
    VINEYARD = _gs("landuse", "vineyard")
    """landuse=vineyard: Wine-grape vineyard."""
    CEMETERY = _gs("landuse", "cemetery")
    """landuse=cemetery: Cemetery or burial ground."""
    ALLOTMENTS = _gs("landuse", "allotments")
    """landuse=allotments: Community allotment garden plots."""

    # ---- shorthands ----
    PARKS = PARK | GARDEN | RECREATION_GROUND | COMMON
    """Public recreational green spaces and commons.

    OSM tags: leisure=park, garden, recreation_ground, common.
    """
    FORESTS = WOOD | FOREST
    """Wooded and forested land from natural and landuse classifications.

    OSM tags: natural=wood; landuse=forest.
    """
    NATURAL = WOOD | SCRUB | GRASSLAND | HEATH | WETLAND
    """Naturally vegetated and semi-natural habitat areas.

    OSM tags: natural=wood, scrub, grassland, heath, wetland.
    """
    PROTECTED = NATURE_RESERVE | WETLAND
    """Conservation-oriented protected or sensitive natural areas.

    OSM tags: leisure=nature_reserve; natural=wetland.
    """
    AGRICULTURAL = MEADOW | GRASS | ORCHARD | VINEYARD | ALLOTMENTS
    """Agricultural and intensively managed green land.

    OSM tags: landuse=meadow, grass, orchard, vineyard, allotments.
    """
    ALL = (
        PARK
        | GARDEN
        | NATURE_RESERVE
        | RECREATION_GROUND
        | COMMON
        | GOLF_COURSE
        | WOOD
        | SCRUB
        | GRASSLAND
        | HEATH
        | WETLAND
        | FOREST
        | MEADOW
        | GRASS
        | ORCHARD
        | VINEYARD
        | CEMETERY
        | ALLOTMENTS
    )
    """All green-space and vegetation categories covered by this module.

    OSM tags: leisure=park, garden, nature_reserve, recreation_ground, common,
    golf_course; natural=wood, scrub, grassland, heath, wetland;
    landuse=forest, meadow, grass, orchard, vineyard, cemetery, allotments.
    """
