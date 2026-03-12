"""Water feature catalog split into polygon fills and linear waterways."""

from osm_to_svg.features.spec import FeatureSpec


def _ww(value: str) -> FeatureSpec:
    """Shorthand for a single waterway= filter (linear waterways)."""
    return FeatureSpec({"waterway": [value]}, needs_areas=False)


def _wp(*clauses: dict[str, list[str]]) -> FeatureSpec:
    """Shorthand for a polygonal water feature using one or more tag clauses."""
    return FeatureSpec(match_clauses=list(clauses), needs_areas=True)


class WATERWAYS:
    """Linear centerline waterways extracted from waterway-tagged OSM ways.

    These specs are intended for stroked rendering of river, stream, canal, and
    drainage centerlines. They target open ways and keep ``needs_areas=False``.
    Some real-world features, notably rivers and canals, also appear in
    ``WATER_POLYGONS`` so they can be rendered as filled area geometries when OSM
    provides polygonal water features.

    Usage::

        from osm_to_svg import features
        mapper.render_features(features.WATERWAYS.ALL, style)
    """

    RIVER = _ww("river")
    """waterway=river: Major natural watercourse centerline; also available as a filled area in WATER_POLYGONS.RIVER."""
    STREAM = _ww("stream")
    """waterway=stream: Minor natural watercourse, smaller than a river."""
    CANAL = _ww("canal")
    """waterway=canal: Artificial navigable waterway centerline; also available as a filled area in WATER_POLYGONS.CANAL."""
    DRAIN = _ww("drain")
    """waterway=drain: Artificial drainage channel, typically not navigable."""
    DITCH = _ww("ditch")
    """waterway=ditch: Small artificial drainage ditch."""
    WEIR = _ww("weir")
    """waterway=weir: Low barrier structure across a stream or river."""
    LOCK = _ww("lock")
    """waterway=lock: Lock chamber segment on a navigable waterway."""
    WATERFALL = _ww("waterfall")
    """waterway=waterfall: Waterfall feature mapped as a linear waterway."""

    ALL = RIVER | STREAM | CANAL | DRAIN | DITCH | WEIR | LOCK | WATERFALL
    """Shorthand for all supported line waterways.

    OSM tags: waterway=river, stream, canal, drain, ditch, weir, lock,
    waterfall.
    """
    FLOWING = RIVER | STREAM | CANAL
    """Shorthand for flowing waterways with a visible channel.

    OSM tags: waterway=river, stream, canal.
    """
    NATURAL = RIVER | STREAM | WATERFALL
    """Shorthand for natural watercourse centerlines.

    OSM tags: waterway=river, stream, waterfall.
    """
    ARTIFICIAL = CANAL | DRAIN | DITCH | WEIR | LOCK
    """Shorthand for human-made linear waterways.

    OSM tags: waterway=canal, drain, ditch, weir, lock.
    """
    DRAINAGE = DRAIN | DITCH
    """Shorthand for narrow drainage-oriented waterways.

    OSM tags: waterway=drain, ditch.
    """
    MAJOR = RIVER | CANAL
    """Shorthand for the most map-prominent linear waterways.

    OSM tags: waterway=river, canal.
    """


class WATER_POLYGONS:
    """Fill-safe water polygons extracted from area or closed-way OSM features.

    These specs are intended for filled rendering of lakes, riverbanks, canal
    basins, wetlands, and other polygonal water features. They enable
    ``needs_areas=True`` so multipolygons are indexed during parsing. Rivers and
    canals intentionally overlap with ``WATERWAYS``: use this namespace when you
    want their area geometry, and ``WATERWAYS`` when you want their centerlines.

    Usage::

        from osm_to_svg import features
        mapper.render_features(features.WATER_POLYGONS.OPEN_WATER, fill_style)
    """

    WATER_AREA = _wp({"natural": ["water"]})
    """natural=water: Generic open-water polygon."""
    LAKE = _wp({"natural": ["water"], "water": ["lake"]})
    """natural=water + water=lake: Lake polygon."""
    RESERVOIR = _wp({"natural": ["water"], "water": ["reservoir"]})
    """natural=water + water=reservoir: Reservoir polygon."""
    POND = _wp({"natural": ["water"], "water": ["pond"]})
    """natural=water + water=pond: Pond polygon."""
    LAGOON = _wp({"natural": ["water"], "water": ["lagoon"]})
    """natural=water + water=lagoon: Lagoon polygon."""
    BASIN = _wp(
        {"landuse": ["basin"]},
        {"natural": ["water"], "water": ["basin"]},
    )
    """landuse=basin or natural=water + water=basin: Basin polygon, usually engineered."""
    SALT_POND = _wp({"landuse": ["salt_pond"]})
    """landuse=salt_pond: Salt evaporation pond or saline basin polygon."""
    RIVER = _wp(
        {"waterway": ["riverbank"]},
        {"natural": ["water"], "water": ["river"]},
    )
    """waterway=riverbank or natural=water + water=river: River area polygon; the same feature is available as a centerline in WATERWAYS.RIVER."""
    CANAL = _wp({"natural": ["water"], "water": ["canal"]})
    """natural=water + water=canal: Canal area polygon; the same feature is available as a centerline in WATERWAYS.CANAL."""
    WETLAND_TYPE = _wp({"natural": ["wetland"]})
    """natural=wetland: Generic wetland polygon; also matches GREEN_SPACES.WETLAND (specific OSM tag value; see WETLANDS for a shorthand group that also encompasses other wetland subtypes such as marsh, swamp, reedbed, and saltmarsh)"""
    MARSH = _wp({"natural": ["wetland"], "wetland": ["marsh"]})
    """natural=wetland + wetland=marsh: Marsh polygon; also semantically valid as green space."""
    SWAMP = _wp({"natural": ["wetland"], "wetland": ["swamp"]})
    """natural=wetland + wetland=swamp: Swamp polygon; also semantically valid as green space."""
    REEDBED = _wp({"natural": ["wetland"], "wetland": ["reedbed"]})
    """natural=wetland + wetland=reedbed: Reedbed polygon; also semantically valid as green space."""
    SALTMARSH = _wp({"natural": ["wetland"], "wetland": ["saltmarsh"]})
    """natural=wetland + wetland=saltmarsh: Saltmarsh polygon; also semantically valid as green space."""
    COASTLINE = _wp({"natural": ["coastline"]})
    """natural=coastline: Coastline or sea-edge polygon when area geometry is present."""

    OPEN_WATER = WATER_AREA | LAKE | RESERVOIR | POND | LAGOON | BASIN | SALT_POND
    """Shorthand for lakes, reservoirs, ponds, lagoons, and other standing open-water polygons."""
    FLOWING = RIVER | CANAL
    """Shorthand for polygonal rivers and canals.

    These overlap with WATERWAYS for centerline rendering.
    """
    WETLANDS = WETLAND_TYPE | MARSH | SWAMP | REEDBED | SALTMARSH
    """Shorthand for wetland and marsh-like polygons."""
    INLAND = OPEN_WATER | FLOWING | WETLANDS
    """Shorthand for inland water polygons, excluding coastline-only geometry."""
    MAJOR_INLAND = LAKE | RESERVOIR | RIVER | CANAL
    """Shorthand for major inland water polygons such as lakes, reservoirs, rivers, and canals."""
    NATURAL = WATER_AREA | LAKE | POND | LAGOON | RIVER | WETLANDS
    """Shorthand for naturally occurring water and wetland polygons."""
    ARTIFICIAL = RESERVOIR | CANAL | BASIN | SALT_POND
    """Shorthand for engineered or strongly human-shaped water polygons."""
