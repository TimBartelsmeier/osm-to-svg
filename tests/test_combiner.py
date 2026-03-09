import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from osm_to_svg.combiner import combine_elements

SVG_NS = "http://www.w3.org/2000/svg"


def _svg(text: str) -> ET.Element:
    return ET.fromstring(text)


def test_combine_elements_rejects_empty_list(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="elements cannot be empty"):
        combine_elements([], str(tmp_path / "out.svg"))


def test_combine_elements_merges_layers_and_background(tmp_path: Path) -> None:
    layer_1 = _svg(
        """
<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"100\" height=\"50\" viewBox=\"0 0 100 50\">
  <defs><clipPath id=\"x\"><rect x=\"0\" y=\"0\" width=\"1\" height=\"1\"/></clipPath></defs>
  <g id=\"roads\"><polyline points=\"0,0 10,10\"/></g>
</svg>
""".strip()
    )
    layer_2 = _svg(
        """
<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"100\" height=\"50\" viewBox=\"0 0 100 50\">
  <title>layer</title>
  <g id=\"buildings\"><rect x=\"1\" y=\"1\" width=\"2\" height=\"2\"/></g>
</svg>
""".strip()
    )

    output = tmp_path / "combined.svg"
    combine_elements([layer_1, layer_2], str(output), background_color="#fff")

    root = ET.parse(output).getroot()
    assert root.attrib["viewBox"] == "0 0 100 50"

    background = root.find(f"{{{SVG_NS}}}rect")
    assert background is not None
    assert background.attrib["fill"] == "#fff"

    groups = [
        elem
        for elem in root.findall(f"{{{SVG_NS}}}g")
        if elem.attrib.get("id", "").startswith("layer-")
    ]
    assert len(groups) == 2


def test_combine_elements_rejects_inconsistent_viewbox(tmp_path: Path) -> None:
    layer_1 = _svg(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50" viewBox="0 0 100 50" />'
    )
    layer_2 = _svg(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50" viewBox="0 0 200 50" />'
    )

    with pytest.raises(ValueError, match="inconsistent viewBox"):
        combine_elements([layer_1, layer_2], str(tmp_path / "out.svg"))
