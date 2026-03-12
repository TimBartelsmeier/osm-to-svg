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

    URBAN = RESIDENTIAL | COMMERCIAL | INDUSTRIAL | RETAIL
    """Shorthand for core urbanized landuse categories.

    OSM tags: landuse=residential, commercial, industrial, retail.
    """
    ALL = URBAN
    """Shorthand for all landuse categories in this module."""
