import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from osm_to_svg.models import Feature, PoiStyle, Style
from osm_to_svg.rendering.renderer import SVGRenderer

SVG_NS = "http://www.w3.org/2000/svg"


def test_render_features_returns_in_memory_element(dummy_transformer) -> None:
    renderer = SVGRenderer(dummy_transformer)
    features = [
        Feature(geometry=[(52.0, 8.0), (52.1, 8.1)], tags={}),
        Feature(
            geometry=[(52.0, 8.0), (52.0, 8.1), (52.1, 8.1), (52.0, 8.0)],
            tags={},
            is_closed=True,
        ),
    ]

    element = renderer.render_features(
        features,
        Style(stroke="#000", fill="none"),
        layer_id="roads",
    )

    assert element is not None
    assert element.tag.endswith("svg")
    groups = element.findall(f"{{{SVG_NS}}}g")
    assert any(group.attrib.get("id") == "roads" for group in groups)


def test_render_features_skips_invalid_geometry(dummy_transformer) -> None:
    renderer = SVGRenderer(dummy_transformer)

    element = renderer.render_features(
        [Feature(geometry=[(52.0, 8.0)], tags={})],
        Style(stroke="#000", fill="none"),
        layer_id="roads",
    )

    assert element is not None
    roads_group = element.find(f"{{{SVG_NS}}}g[@id='roads']")
    assert roads_group is not None
    assert len(list(roads_group)) == 0


def test_render_features_sanitizes_invalid_layer_id(dummy_transformer) -> None:
    renderer = SVGRenderer(dummy_transformer)

    element = renderer.render_features(
        [Feature(geometry=[(52.0, 8.0), (52.1, 8.1)], tags={})],
        Style(stroke="#000", fill="none"),
        layer_id="0 highway",
    )

    sanitized_group = element.find(f"{{{SVG_NS}}}g[@id='layer-0-highway']")
    assert sanitized_group is not None


def test_place_poi_markers_requires_exactly_one_sizing_method(
    dummy_transformer,
    marker_svg_path: Path,
) -> None:
    renderer = SVGRenderer(dummy_transformer)

    with pytest.raises(ValueError, match="Must specify"):
        renderer.place_poi_markers(
            coords=[(52.0, 8.0)],
            poi_style=PoiStyle(marker_svg_path=str(marker_svg_path)),
        )

    with pytest.raises(ValueError, match="Cannot specify multiple"):
        renderer.place_poi_markers(
            coords=[(52.0, 8.0)],
            poi_style=PoiStyle(
                marker_svg_path=str(marker_svg_path), scale=1.0, width_meters=20.0
            ),
        )


def test_place_poi_markers_returns_in_memory_element(
    dummy_transformer,
    marker_svg_path: Path,
) -> None:
    renderer = SVGRenderer(dummy_transformer)

    element = renderer.place_poi_markers(
        coords=[(52.0, 8.0)],
        poi_style=PoiStyle(marker_svg_path=str(marker_svg_path), width_meters=25.0),
    )

    assert element is not None
    assert element.tag.endswith("svg")
    pois_group = element.find(f"{{{SVG_NS}}}g[@id='pois']")
    assert pois_group is not None


def test_place_poi_markers_supports_height_meters(
    dummy_transformer,
    marker_svg_path: Path,
) -> None:
    renderer = SVGRenderer(dummy_transformer)

    element = renderer.place_poi_markers(
        coords=[(52.0, 8.0)],
        poi_style=PoiStyle(marker_svg_path=str(marker_svg_path), height_meters=10.0),
    )

    assert element is not None


class ProgressSpy:
    def __init__(self) -> None:
        self.updates: list[int] = []

    def update(self, value: int) -> None:
        self.updates.append(value)


def test_place_poi_markers_sanitizes_invalid_layer_id(
    dummy_transformer,
    marker_svg_path: Path,
) -> None:
    renderer = SVGRenderer(dummy_transformer)

    element = renderer.place_poi_markers(
        coords=[(52.0, 8.0)],
        poi_style=PoiStyle(marker_svg_path=str(marker_svg_path), scale=1.0),
        layer_id="0 pois",
    )

    sanitized_group = element.find(f"{{{SVG_NS}}}g[@id='layer-0-pois']")
    assert sanitized_group is not None


def test_renderer_updates_progress_bar_for_features_and_pois(
    dummy_transformer,
    marker_svg_path: Path,
) -> None:
    renderer = SVGRenderer(dummy_transformer)

    feature_progress = ProgressSpy()
    poi_progress = ProgressSpy()

    feature_element = renderer.render_features(
        [
            Feature(geometry=[(52.0, 8.0)], tags={}),
            Feature(geometry=[(52.0, 8.0), (52.1, 8.1)], tags={}),
        ],
        Style(stroke="#000", fill="none"),
        _progress_bar=feature_progress,
    )
    poi_element = renderer.place_poi_markers(
        coords=[(52.0, 8.0), (52.1, 8.1)],
        poi_style=PoiStyle(marker_svg_path=str(marker_svg_path), scale=1.0),
        _progress_bar=poi_progress,
    )

    assert feature_element is not None
    assert poi_element is not None
    assert feature_progress.updates == [1, 1]
    assert poi_progress.updates == [1, 1]


def test_sanitize_svg_id_uses_prefix_for_empty_or_invalid_values(
    dummy_transformer,
) -> None:
    renderer = SVGRenderer(dummy_transformer)

    assert renderer._sanitize_svg_id("   ", prefix="clip") == "clip"
    assert renderer._sanitize_svg_id("---", prefix="clip") == "clip"


@pytest.mark.parametrize(
    ("anchor", "expected"),
    [
        ("center", (95.0, 40.0)),
        ("top", (95.0, 50.0)),
        ("top-right", (90.0, 50.0)),
        ("right", (90.0, 40.0)),
        ("bottom-right", (90.0, 30.0)),
        ("bottom", (95.0, 30.0)),
        ("bottom-left", (100.0, 30.0)),
        ("left", (100.0, 40.0)),
        ("top-left", (100.0, 50.0)),
    ],
)
def test_calculate_anchor_offset_variants(dummy_transformer, anchor, expected) -> None:  # noqa: ANN001
    renderer = SVGRenderer(dummy_transformer)
    assert (
        renderer._calculate_anchor_offset(100.0, 50.0, 10.0, 20.0, 1.0, anchor)
        == expected
    )


def test_calculate_anchor_offset_falls_back_to_center_for_unknown_anchor(
    dummy_transformer,
) -> None:
    renderer = SVGRenderer(dummy_transformer)
    assert renderer._calculate_anchor_offset(
        100.0, 50.0, 10.0, 20.0, 1.0, "unknown"
    ) == (
        95.0,
        40.0,
    )


def test_parse_dimension_handles_number_and_invalid_string(dummy_transformer) -> None:
    renderer = SVGRenderer(dummy_transformer)
    assert renderer._parse_svg_dimension("12px") == 12.0
    assert renderer._parse_dimension(12) == 12.0
    assert renderer._parse_dimension("15pt") == 15.0
    assert renderer._parse_dimension("invalid") == 24.0


def test_copy_element_handles_supported_svg_nodes(
    dummy_transformer,
    tmp_path: Path,
) -> None:
    renderer = SVGRenderer(dummy_transformer)
    path = tmp_path / "marker-mixed.svg"
    path.write_text(
        """
<svg xmlns="http://www.w3.org/2000/svg" width="10" height="20">
  <g id="root-group">
    <circle cx="2" cy="2" r="1" />
    <rect x="0" y="0" width="5" height="5" />
    <path d="M 0 0 L 5 5" />
    <line x1="0" y1="0" x2="1" y2="1" />
  </g>
</svg>
""".strip(),
        encoding="utf-8",
    )

    root = ET.parse(path).getroot()
    # Use svgwrite drawing/group as expected by _copy_element
    import svgwrite

    dwg = svgwrite.Drawing(":memory:")
    group = dwg.g(id="target")
    for child in root:
        renderer._copy_element(child, group, dwg)

    # Supported elements (including <line>) should be copied.
    assert len(group.elements) >= 1
    serialized = "\n".join(element.tostring() for element in group.elements)
    assert "<line" in serialized


def test_copy_element_supports_polyline_polygon_and_ellipse(
    dummy_transformer,
    tmp_path: Path,
) -> None:
    renderer = SVGRenderer(dummy_transformer)
    path = tmp_path / "marker-shapes.svg"
    path.write_text(
        """
<svg xmlns="http://www.w3.org/2000/svg" width="10" height="20">
  <polyline points="0,0 5,5 9,1" />
  <polygon points="1,1 3,1 2,3" />
  <ellipse cx="5" cy="5" rx="2" ry="1" />
</svg>
""".strip(),
        encoding="utf-8",
    )

    root = ET.parse(path).getroot()
    import svgwrite

    dwg = svgwrite.Drawing(":memory:")
    group = dwg.g(id="target")
    for child in root:
        renderer._copy_element(child, group, dwg)

    serialized = "\n".join(element.tostring() for element in group.elements)
    assert "<polyline" in serialized
    assert "<polygon" in serialized
    assert "<ellipse" in serialized
