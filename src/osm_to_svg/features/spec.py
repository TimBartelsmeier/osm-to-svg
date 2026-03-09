"""Core feature specification helpers.

Helper naming convention used in the feature catalog modules:
- ``_r(value)``: ``highway=value``
- ``_rw(value)``: ``railway=value``
- ``_w(value)``: ``waterway=value``
- ``_wb(value)``: ``natural=value`` for water-body area matching
- ``_b(value)``: ``building=value``
- ``_gs(key, value)``: generic tag-key/value matcher for green-space specs
"""

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

    def __or__(self, other: "FeatureSpec") -> "FeatureSpec":
        merged: dict[str, list[str]] = {}
        for key in set(self.tag_filters) | set(other.tag_filters):
            merged[key] = list(
                dict.fromkeys(
                    self.tag_filters.get(key, []) + other.tag_filters.get(key, [])
                )
            )
        return FeatureSpec(merged, self.needs_areas or other.needs_areas)
