"""Green-space feature catalog (OSM leisure=, natural=, landuse=)."""

from osm_to_svg.features.spec import FeatureSpec


def _gs(tag_key: str, value: str) -> FeatureSpec:
    """Shorthand for a green space filter with an explicit tag key."""
    return FeatureSpec({tag_key: [value]}, needs_areas=True)


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
