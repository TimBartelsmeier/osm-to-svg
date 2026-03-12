"""Core feature specification helpers.

Helper naming convention used in the feature catalog modules:
- ``_r(value)``: ``highway=value``
- ``_rw(value)``: ``railway=value``
- ``_w(value)``: ``waterway=value``
- ``_wa(...)``: water area matching with optional secondary tags
- ``_b(value)``: ``building=value``
- ``_gs(key, value)``: generic tag-key/value matcher for green-space specs
"""

from __future__ import annotations

from dataclasses import dataclass, field


def _merge_tag_filters(*filters: dict[str, list[str]]) -> dict[str, list[str]]:
    """Merge tag filters while preserving value order and removing duplicates."""
    merged: dict[str, list[str]] = {}
    for tag_filter in filters:
        for key, values in tag_filter.items():
            merged.setdefault(key, [])
            merged[key].extend(values)

    return {key: list(dict.fromkeys(values)) for key, values in merged.items()}


def _normalize_clause(
    clause: dict[str, list[str]],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Return a hashable form of a match clause for deduplication."""
    return tuple(sorted((key, tuple(values)) for key, values in clause.items()))


@dataclass
class FeatureSpec:
    """Specifies which OSM features to extract, as a set of tag filters.

    tag_filters maps OSM tag keys to lists of accepted values (OR semantics).
    match_clauses stores the actual matching rules. Within one clause, all tag
    keys must match and each key accepts any of its listed values. Across clauses,
    matching uses OR semantics. This allows specs such as ``natural=water`` AND
    ``water=lake`` while preserving the existing ``|`` union behavior.
    needs_areas enables multipolygon/area processing during PBF parsing, which
    is required for features that appear as closed areas (buildings, water bodies,
    green spaces) rather than plain ways.

    Specs can be combined with | to create a union that matches either.

    Example:
        >>> from osm_to_svg import features
        >>> spec = features.ROADS.MAJOR | features.WATER_POLYGONS.OPEN_WATER
        >>> mapper.render_features(spec, style)
    """

    tag_filters: dict[str, list[str]] = field(default_factory=dict)
    match_clauses: list[dict[str, list[str]]] = field(default_factory=list)
    needs_areas: bool = False

    def __post_init__(self) -> None:
        if self.match_clauses:
            self.match_clauses = [
                {key: list(dict.fromkeys(values)) for key, values in clause.items()}
                for clause in self.match_clauses
            ]
            self.tag_filters = _merge_tag_filters(*self.match_clauses)
            return

        if self.tag_filters:
            normalized = {
                key: list(dict.fromkeys(values))
                for key, values in self.tag_filters.items()
            }
            self.tag_filters = normalized
            self.match_clauses = [normalized]

    def __or__(self, other: "FeatureSpec") -> "FeatureSpec":
        merged = _merge_tag_filters(self.tag_filters, other.tag_filters)
        match_clauses: list[dict[str, list[str]]] = []
        seen: set[tuple[tuple[str, tuple[str, ...]], ...]] = set()

        for clause in self.match_clauses + other.match_clauses:
            normalized = _normalize_clause(clause)
            if normalized in seen:
                continue
            seen.add(normalized)
            match_clauses.append(clause)

        return FeatureSpec(
            tag_filters=merged,
            match_clauses=match_clauses,
            needs_areas=self.needs_areas or other.needs_areas,
        )
