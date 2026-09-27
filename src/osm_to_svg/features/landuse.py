"""Landuse feature catalog (OSM landuse=)."""

from osm_to_svg.features.spec import FeatureSpec


def _lu(value: str) -> FeatureSpec:
    """Shorthand for a single landuse= filter."""
    return FeatureSpec({"landuse": [value]}, needs_areas=True)


class LANDUSE:
    """Urban and managed landuse features.

    These features are polygon-oriented and require area processing.

    Usage::

        from osm_to_svg import features
        mapper.render_features(features.LANDUSE.URBAN, style)
    """

    RESIDENTIAL = _lu("residential")
    """landuse=residential: Predominantly residential landuse polygon."""
    COMMERCIAL = _lu("commercial")
    """landuse=commercial: Predominantly commercial landuse polygon."""
    INDUSTRIAL = _lu("industrial")
    """landuse=industrial: Predominantly industrial landuse polygon."""
    RETAIL = _lu("retail")
    """landuse=retail: Retail-focused landuse polygon."""
    CONSTRUCTION = _lu("construction")
    """landuse=construction: Site under active development."""
    EDUCATION = _lu("education")
    """landuse=education: Land predominantly used for education facilities."""
    INSTITUTIONAL = _lu("institutional")
    """landuse=institutional: Land used for institutional purposes."""
    FARMLAND = _lu("farmland")
    """landuse=farmland: Cropland used for tillage and production."""
    FARMYARD = _lu("farmyard")
    """landuse=farmyard: Farm buildings and surrounding yard."""
    GREENHOUSE_HORTICULTURE = _lu("greenhouse_horticulture")
    """landuse=greenhouse_horticulture: Area used for greenhouse growing."""
    RAILWAY = _lu("railway")
    """landuse=railway: Land used around railways and railway stations."""
    HIGHWAY = _lu("highway")
    """landuse=highway: Land occupied by a highway and its auxiliaries."""
    PORT = _lu("port")
    """landuse=port: Coastal industrial land used for handling vessels."""
    QUARRY = _lu("quarry")
    """landuse=quarry: Surface mineral extraction area."""
    LANDFILL = _lu("landfill")
    """landuse=landfill: Area where waste is deposited."""
    MILITARY = _lu("military")
    """landuse=military: Land owned or used by the military."""
    RELIGIOUS = _lu("religious")
    """landuse=religious: Area used for religious purposes."""
    RECREATION_GROUND = _lu("recreation_ground")
    """landuse=recreation_ground: Open green space for general recreation."""
    CEMETERY = _lu("cemetery")
    """landuse=cemetery: Burial ground."""
    GRASS = _lu("grass")
    """landuse=grass: Managed grass area."""
    FOREST = _lu("forest")
    """landuse=forest: Managed forest or woodland plantation."""
    MEADOW = _lu("meadow")
    """landuse=meadow: Grassland used for hay or grazing."""
    ORCHARD = _lu("orchard")
    """landuse=orchard: Managed fruit or nut tree planting."""
    VINEYARD = _lu("vineyard")
    """landuse=vineyard: Land used to grow grapes."""
    ALLOTMENTS = _lu("allotments")
    """landuse=allotments: Community garden plots."""
    BASIN = _lu("basin")
    """landuse=basin: Artificially graded area that holds water."""
    SALT_POND = _lu("salt_pond")
    """landuse=salt_pond: Salt evaporation pond."""

    URBAN = (
        RESIDENTIAL
        | COMMERCIAL
        | INDUSTRIAL
        | RETAIL
        | CONSTRUCTION
        | EDUCATION
        | INSTITUTIONAL
    )
    """Shorthand for core urbanized landuse categories.

    OSM tags: landuse=residential, commercial, industrial, retail.
    """
    AGRICULTURAL = (
        FARMLAND
        | FARMYARD
        | GREENHOUSE_HORTICULTURE
        | FOREST
        | MEADOW
        | ORCHARD
        | VINEYARD
        | ALLOTMENTS
    )
    """Shorthand for agricultural and managed rural landuse."""
    TRANSPORT = RAILWAY | HIGHWAY | PORT
    """Shorthand for transport-related landuse."""
    AMENITY = QUARRY | LANDFILL | MILITARY | RELIGIOUS | RECREATION_GROUND | CEMETERY
    """Shorthand for civic, recreational, extraction, and service landuse."""
    NATURALIZED = GRASS | FOREST | MEADOW | ORCHARD | VINEYARD | ALLOTMENTS
    """Shorthand for vegetated landuse categories."""
    WATER = BASIN | SALT_POND
    """Shorthand for water-related landuse."""
    ALL = URBAN | AGRICULTURAL | TRANSPORT | AMENITY | NATURALIZED | WATER
    """Shorthand for every landuse value in this module."""
