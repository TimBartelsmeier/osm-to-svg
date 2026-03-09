import xml.etree.ElementTree as ET

import svgwrite

from osm_to_svg.rendering.svg_utils import (
    _parse_points,
    copy_svg_element,
    parse_svg_dimension,
)


def test_parse_svg_dimension_uses_fallback_for_invalid_values() -> None:
    assert parse_svg_dimension("bad", fallback=42.0) == 42.0


def test_parse_points_handles_short_and_invalid_tokens() -> None:
    assert _parse_points("") == []
    assert _parse_points("1") == []
    assert _parse_points("1,2 x,y 3,4") == [(1.0, 2.0), (3.0, 4.0)]


def test_copy_svg_element_handles_polyline_with_missing_points_attr() -> None:
    element = ET.fromstring('<polyline xmlns="http://www.w3.org/2000/svg" />')
    dwg = svgwrite.Drawing(":memory:")
    group = dwg.g(id="target")

    copy_svg_element(element, group, dwg)

    assert len(group.elements) == 1
