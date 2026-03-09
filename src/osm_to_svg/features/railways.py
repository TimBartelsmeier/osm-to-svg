"""Railway feature catalog (OSM railway=)."""

from osm_to_svg.features.spec import FeatureSpec


def _rw(value: str) -> FeatureSpec:
    """Shorthand for a single railway= filter."""
    return FeatureSpec({"railway": [value]})


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
