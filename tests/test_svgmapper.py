import xml.etree.ElementTree as ET
from importlib import import_module
from pathlib import Path

import pytest

mapper_module = import_module("osm_to_svg.SvgMapper")
from osm_to_svg import features
from osm_to_svg.features import FeatureSpec
from osm_to_svg.models import PoiStyle, Style
from osm_to_svg.SvgMapper import SvgMapper


class DummyParser:
    def __init__(self, pbf_path: str):
        self.pbf_path = pbf_path

    def get_bounds(self) -> tuple[float, float, float, float]:
        return (8.0, 52.0, 8.2, 52.2)

    def extract_features(self, spec: FeatureSpec):  # noqa: ANN001
        return []


class DummyCoordinateTransformer:
    def __init__(self, bounds, scale: int = 100000, dpi: int = 96):  # noqa: ANN001
        self.geo_bounds = bounds
        self.scale = scale
        self.dpi = dpi

    def get_dimensions(self) -> tuple[int, int]:
        return (200, 100)


class DummyRenderer:
    def __init__(self, transformer, background_color=None):  # noqa: ANN001
        self.transformer = transformer
        self.background_color = background_color

    def render_features(self, features, style, layer_id):  # noqa: ANN001
        return ET.Element("svg")

    def place_poi_markers(
        self,
        coords,  # noqa: ANN001
        poi_style,  # noqa: ANN001
        layer_id="pois",  # noqa: ANN001
    ):
        return ET.Element("svg")


@pytest.fixture
def pbf_path(tmp_path: Path) -> Path:
    file_path = tmp_path / "sample.osm.pbf"
    file_path.write_bytes(b"not-a-real-pbf")
    return file_path


@pytest.fixture
def patched_svgmapper_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mapper_module, "PBFParser", DummyParser)
    monkeypatch.setattr(
        mapper_module, "CoordinateTransformer", DummyCoordinateTransformer
    )
    monkeypatch.setattr(mapper_module, "SVGRenderer", DummyRenderer)


def test_svgmapper_enforces_context_manager_for_rendering(
    pbf_path: Path,
    patched_svgmapper_dependencies,
) -> None:
    mapper = SvgMapper(str(pbf_path))

    with pytest.raises(RuntimeError, match="context manager"):
        mapper.render_features(features.ROADS.MAJOR, Style(stroke="#000"))


def test_svgmapper_gets_bounds_inside_context(
    pbf_path: Path,
    patched_svgmapper_dependencies,
) -> None:
    with SvgMapper(str(pbf_path)) as mapper:
        assert mapper.get_bounds() == (8.0, 52.0, 8.2, 52.2)
        assert mapper.get_dimensions() == (200, 100)


def test_save_uses_accumulated_in_memory_layers(
    pbf_path: Path,
    marker_svg_path: Path,
    patched_svgmapper_dependencies,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_combine_elements(
        elements: list[ET.Element],
        output_path: str,
        background_color: str | None = None,
    ) -> None:
        captured["elements"] = elements
        captured["output_path"] = output_path
        captured["background_color"] = background_color

    monkeypatch.setattr(mapper_module, "combine_elements", fake_combine_elements)

    with SvgMapper(str(pbf_path), background_color="#ffffff") as mapper:
        mapper.render_features(features.ROADS.MAJOR, Style(stroke="#000"))
        mapper.place_poi_markers(
            coords=[(52.0, 8.0)],
            poi_style=PoiStyle(marker_svg_path=str(marker_svg_path), scale=1.0),
        )
        mapper.save("combined.svg")

    assert len(captured["elements"]) == 2
    assert captured["output_path"] == "combined.svg"
    assert captured["background_color"] == "#ffffff"


def test_save_raises_when_no_layers(
    pbf_path: Path,
    patched_svgmapper_dependencies,
) -> None:
    with SvgMapper(str(pbf_path)) as mapper:
        with pytest.raises(ValueError, match="No layers to combine"):
            mapper.save("combined.svg")


def test_svgmapper_raises_for_missing_pbf_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="PBF file not found"):
        SvgMapper(str(tmp_path / "missing.osm.pbf"))


def test_svgmapper_uses_custom_bounds_when_provided(
    pbf_path: Path,
    patched_svgmapper_dependencies,
) -> None:
    custom_bounds = (1.0, 2.0, 3.0, 4.0)
    with SvgMapper(str(pbf_path), bounds=custom_bounds) as mapper:
        assert mapper.get_bounds() == custom_bounds


def test_svgmapper_place_poi_requires_context(
    pbf_path: Path,
    marker_svg_path: Path,
    patched_svgmapper_dependencies,
) -> None:
    mapper = SvgMapper(str(pbf_path))
    with pytest.raises(RuntimeError, match="context manager"):
        mapper.place_poi_markers(
            coords=[(52.0, 8.0)],
            poi_style=PoiStyle(marker_svg_path=str(marker_svg_path), scale=1.0),
        )


def test_svgmapper_place_poi_raises_for_missing_marker(
    pbf_path: Path,
    patched_svgmapper_dependencies,
    tmp_path: Path,
) -> None:
    with SvgMapper(str(pbf_path)) as mapper:
        with pytest.raises(FileNotFoundError, match="Marker SVG file not found"):
            mapper.place_poi_markers(
                coords=[(52.0, 8.0)],
                poi_style=PoiStyle(
                    marker_svg_path=str(tmp_path / "missing.svg"), scale=1.0
                ),
            )


def test_svgmapper_getters_require_context(
    pbf_path: Path,
    patched_svgmapper_dependencies,
) -> None:
    mapper = SvgMapper(str(pbf_path))

    with pytest.raises(RuntimeError, match="context manager"):
        mapper.get_bounds()

    with pytest.raises(RuntimeError, match="context manager"):
        mapper.get_dimensions()


# --- layer ID generation ---


def _capture_render_layer_ids(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Patch DummyRenderer to record layer_id values passed to render_features/place_poi_markers."""
    captured: list[str] = []
    original_render = DummyRenderer.render_features
    original_poi = DummyRenderer.place_poi_markers

    def spy_render(self, features, style, layer_id):  # noqa: ANN001
        captured.append(layer_id)
        return original_render(self, features, style, layer_id)

    def spy_poi(
        self,
        coords,
        poi_style,
        layer_id="pois",
    ):
        captured.append(layer_id)
        return original_poi(
            self,
            coords,
            poi_style,
            layer_id,
        )

    monkeypatch.setattr(DummyRenderer, "render_features", spy_render)
    monkeypatch.setattr(DummyRenderer, "place_poi_markers", spy_poi)
    return captured


def test_layer_id_default_uses_tag_key_with_index(
    pbf_path: Path,
    patched_svgmapper_dependencies,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_render_layer_ids(monkeypatch)

    with SvgMapper(str(pbf_path)) as mapper:
        mapper.render_features(features.ROADS.MAJOR, Style(stroke="#000"))

    assert captured == ["0 highway"]


def test_layer_id_explicit_value_gets_prefixed_with_index(
    pbf_path: Path,
    patched_svgmapper_dependencies,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_render_layer_ids(monkeypatch)

    with SvgMapper(str(pbf_path)) as mapper:
        mapper.render_features(
            features.ROADS.MAJOR, Style(stroke="#000"), layer_id="roads"
        )

    assert captured == ["0 roads"]


def test_layer_id_sequential_calls_increment_index(
    pbf_path: Path,
    patched_svgmapper_dependencies,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_render_layer_ids(monkeypatch)

    with SvgMapper(str(pbf_path)) as mapper:
        mapper.render_features(features.ROADS.MAJOR, Style(stroke="#000"))
        mapper.render_features(features.ROADS.MAJOR, Style(stroke="#FF0000"))

    assert captured == ["0 highway", "1 highway"]


def test_layer_id_combined_features_joins_tag_keys(
    pbf_path: Path,
    patched_svgmapper_dependencies,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_render_layer_ids(monkeypatch)

    with SvgMapper(str(pbf_path)) as mapper:
        mapper.render_features(
            features.ROADS.MAJOR | features.BUILDINGS.YES,
            Style(stroke="#000"),
        )

    assert captured == ["0 building_highway"]


def test_layer_id_poi_markers_uses_pois_with_index(
    pbf_path: Path,
    marker_svg_path: Path,
    patched_svgmapper_dependencies,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_render_layer_ids(monkeypatch)

    with SvgMapper(str(pbf_path)) as mapper:
        mapper.render_features(features.ROADS.MAJOR, Style(stroke="#000"))
        mapper.place_poi_markers(
            coords=[(52.0, 8.0)],
            poi_style=PoiStyle(marker_svg_path=str(marker_svg_path), scale=1.0),
        )

    assert captured == ["0 highway", "1 pois"]


def test_layer_id_poi_markers_explicit_value_gets_prefixed_with_index(
    pbf_path: Path,
    marker_svg_path: Path,
    patched_svgmapper_dependencies,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_render_layer_ids(monkeypatch)

    with SvgMapper(str(pbf_path)) as mapper:
        mapper.render_features(features.ROADS.MAJOR, Style(stroke="#000"))
        mapper.place_poi_markers(
            coords=[(52.0, 8.0)],
            poi_style=PoiStyle(marker_svg_path=str(marker_svg_path), scale=1.0),
            layer_id="landmarks",
        )

    assert captured == ["0 highway", "1 landmarks"]
