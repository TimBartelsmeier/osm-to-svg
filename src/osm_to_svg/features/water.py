"""Water feature catalog (OSM waterway= and natural=)."""

from osm_to_svg.features.spec import FeatureSpec


def _w(value: str) -> FeatureSpec:
    """Shorthand for a single waterway= filter (linear waterways)."""
    return FeatureSpec({"waterway": [value]}, needs_areas=False)


def _wb(natural_value: str) -> FeatureSpec:
    """Shorthand for a water body via natural= tag (areas)."""
    return FeatureSpec({"natural": [natural_value]}, needs_areas=True)


class WATER:
    """Waterway and water body features.

    Linear waterways (RIVER, STREAM, ...) use way geometry (needs_areas=False).
    Water bodies (WATER_AREA, LAKE, ...) use area/polygon geometry (needs_areas=True).

    Note: LAKE, RESERVOIR, and POND all map to natural=water with identical
    filters. OSM stores these as secondary ``water=`` sub-types, which are not
    AND-filtered here. They are separate named specs for discoverability but
    functionally equivalent; use WATER_AREA or BODIES for generic rendering.

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
    WATER_AREA = _wb("water")
    """natural=water: Generic standing water area. The water= sub-type (lake, pond, reservoir) is not filterable here."""
    LAKE = _wb("water")
    """natural=water (+ water=lake): Lake; the water= sub-type is not filterable here - equivalent to WATER_AREA."""
    RESERVOIR = _wb("water")
    """natural=water (+ water=reservoir): Artificial water reservoir; the water= sub-type is not filterable here - equivalent to WATER_AREA."""
    POND = _wb("water")
    """natural=water (+ water=pond): Small pond; the water= sub-type is not filterable here - equivalent to WATER_AREA."""
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
