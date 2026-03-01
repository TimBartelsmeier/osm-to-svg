import xml.etree.ElementTree as ET
from importlib import import_module
from pathlib import Path

import pytest

mapper_module = import_module("osm_to_svg.SvgMapper")
from osm_to_svg.features import RoadType
from osm_to_svg.models import Style
from osm_to_svg.SvgMapper import SvgMapper


class DummyParser:
    def __init__(self, pbf_path: str):
        self.pbf_path = pbf_path

    def get_bounds(self) -> tuple[float, float, float, float]:
        return (8.0, 52.0, 8.2, 52.2)

    def extract_features(self, feature_type, subtypes):  # noqa: ANN001
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

    def render_features(self, features, style, output_path, layer_id):  # noqa: ANN001
        if output_path is None:
            return ET.Element("svg")
        return None

    def place_poi_markers(
        self,
        marker_svg_path,  # noqa: ANN001
        coords,  # noqa: ANN001
        scale=None,  # noqa: ANN001
        output_path=None,
        anchor="center",  # noqa: ANN001
        width_meters=None,  # noqa: ANN001
        height_meters=None,  # noqa: ANN001
    ):
        if output_path is None:
            return ET.Element("svg")
        return None


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
        mapper.render_features(RoadType, None, Style(stroke="#000"))


def test_svgmapper_gets_bounds_inside_context(
    pbf_path: Path,
    patched_svgmapper_dependencies,
) -> None:
    with SvgMapper(str(pbf_path)) as mapper:
        assert mapper.get_bounds() == (8.0, 52.0, 8.2, 52.2)
        assert mapper.get_dimensions() == (200, 100)


def test_save_combined_uses_accumulated_in_memory_layers(
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
        mapper.render_features(RoadType, None, Style(stroke="#000"), output_path=None)
        mapper.place_poi_markers(
            str(marker_svg_path),
            coords=[(52.0, 8.0)],
            scale=1.0,
            output_path=None,
        )
        mapper.save_combined("combined.svg")

    assert len(captured["elements"]) == 2
    assert captured["output_path"] == "combined.svg"
    assert captured["background_color"] == "#ffffff"


def test_save_combined_raises_when_no_layers(
    pbf_path: Path,
    patched_svgmapper_dependencies,
) -> None:
    with SvgMapper(str(pbf_path)) as mapper:
        with pytest.raises(ValueError, match="No layers to combine"):
            mapper.save_combined("combined.svg")


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
        mapper.place_poi_markers(str(marker_svg_path), coords=[(52.0, 8.0)], scale=1.0)


def test_svgmapper_place_poi_raises_for_missing_marker(
    pbf_path: Path,
    patched_svgmapper_dependencies,
    tmp_path: Path,
) -> None:
    with SvgMapper(str(pbf_path)) as mapper:
        with pytest.raises(FileNotFoundError, match="Marker SVG file not found"):
            mapper.place_poi_markers(
                str(tmp_path / "missing.svg"),
                coords=[(52.0, 8.0)],
                scale=1.0,
            )


def test_svgmapper_combine_delegates_to_combine_svgs(
    pbf_path: Path,
    patched_svgmapper_dependencies,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_combine_svgs(svg_paths: list[str], output_path: str) -> None:
        captured["svg_paths"] = svg_paths
        captured["output_path"] = output_path

    monkeypatch.setattr(mapper_module, "combine_svgs", fake_combine_svgs)

    with SvgMapper(str(pbf_path)) as mapper:
        mapper.combine(["a.svg", "b.svg"], "out.svg")

    assert captured["svg_paths"] == ["a.svg", "b.svg"]
    assert captured["output_path"] == "out.svg"


def test_svgmapper_getters_require_context(
    pbf_path: Path,
    patched_svgmapper_dependencies,
) -> None:
    mapper = SvgMapper(str(pbf_path))

    with pytest.raises(RuntimeError, match="context manager"):
        mapper.get_bounds()

    with pytest.raises(RuntimeError, match="context manager"):
        mapper.get_dimensions()
