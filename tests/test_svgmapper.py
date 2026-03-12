import xml.etree.ElementTree as ET
from importlib import import_module
from pathlib import Path

import pytest

mapper_module = import_module("osm_to_svg.mapper")
create_map_module = import_module("osm_to_svg.create_map")
from osm_to_svg import features
from osm_to_svg.create_map import create_map
from osm_to_svg.features import FeatureSpec
from osm_to_svg.mapper import SvgMapper
from osm_to_svg.models import PoiStyle, Style


class DummyParser:
    def __init__(self, pbf_path: str):
        self.pbf_path = pbf_path

    def get_bounds(self) -> tuple[float, float, float, float]:
        return (52.0, 8.0, 52.2, 8.2)

    def extract_features(self, spec: FeatureSpec):  # noqa: ANN001
        return []


class DummyCoordinateTransformer:
    def __init__(self, bounds, scale: int = 100000, dpi: int = 300):  # noqa: ANN001
        self.geo_bounds = bounds
        self.scale = scale
        self.dpi = dpi

    def get_dimensions(self) -> tuple[int, int]:
        return (200, 100)


class DummyRenderer:
    def __init__(self, transformer, background_color=None):  # noqa: ANN001
        self.transformer = transformer
        self.background_color = background_color

    def render_features(self, features, style, layer_id, _progress_bar=None):  # noqa: ANN001
        return ET.Element("svg")

    def place_poi_markers(
        self,
        coords,  # noqa: ANN001
        poi_style,  # noqa: ANN001
        layer_id="pois",  # noqa: ANN001
        _progress_bar=None,
    ):
        return ET.Element("svg")


class ProgressSpy:
    def __init__(self) -> None:
        self.descriptions: list[str] = []
        self.n = -1
        self.total = -1
        self.refresh_calls = 0

    def set_description(self, value: str) -> None:
        self.descriptions.append(value)

    def refresh(self) -> None:
        self.refresh_calls += 1


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
        assert mapper.get_bounds() == (52.0, 8.0, 52.2, 8.2)
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

    def spy_render(self, features, style, layer_id, _progress_bar=None):  # noqa: ANN001
        captured.append(layer_id)
        return original_render(self, features, style, layer_id)

    def spy_poi(
        self,
        coords,
        poi_style,
        layer_id="pois",
        _progress_bar=None,
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


def test_create_map_uses_svgmapper_workflow(
    pbf_path: Path,
    marker_svg_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []

    class SpyMapper:
        def __init__(
            self,
            pbf_path: str,
            scale: int = 100000,
            dpi: int = 300,
            bounds: tuple[float, float, float, float] | None = None,
            background_color: str | None = None,
        ):
            calls.append(
                (
                    "init",
                    {
                        "pbf_path": pbf_path,
                        "scale": scale,
                        "dpi": dpi,
                        "bounds": bounds,
                        "background_color": background_color,
                    },
                )
            )

        def __enter__(self):
            calls.append(("enter", None))
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: ANN001
            calls.append(("exit", None))

        def render_features(
            self, feature_spec: FeatureSpec, style: Style, _progress_bar=None
        ) -> None:
            calls.append(("render_features", (feature_spec, style)))

        def place_poi_markers(
            self,
            coords: list[tuple[float, float]],
            poi_style: PoiStyle,
            _progress_bar=None,
        ) -> None:
            calls.append(("place_poi_markers", (coords, poi_style)))

        def save(self, output_path: str) -> None:
            calls.append(("save", output_path))

    monkeypatch.setattr(create_map_module, "SvgMapper", SpyMapper)

    feature_layers = [
        (features.WATER_POLYGONS.OPEN_WATER, Style(fill="#4A90E2")),
        (features.ROADS.MAJOR, Style(stroke="#000000", stroke_width=1.0)),
    ]
    poi_layers = [
        (
            [(52.0, 8.0)],
            PoiStyle(marker_svg_path=str(marker_svg_path), scale=1.0),
        )
    ]

    create_map(
        pbf_path=str(pbf_path),
        scale=75000,
        dpi=300,
        bounds=(9.6, 52.3, 9.8, 52.5),
        background_color="#FFFFFF",
        feature_layers=feature_layers,
        poi_layers=poi_layers,
        output_path="result.svg",
    )

    assert calls[0] == (
        "init",
        {
            "pbf_path": str(pbf_path),
            "scale": 75000,
            "dpi": 300,
            "bounds": (9.6, 52.3, 9.8, 52.5),
            "background_color": "#FFFFFF",
        },
    )
    assert calls[1][0] == "enter"
    assert [name for name, _ in calls] == [
        "init",
        "enter",
        "render_features",
        "render_features",
        "place_poi_markers",
        "save",
        "exit",
    ]
    assert calls[2][1] == feature_layers[0]
    assert calls[3][1] == feature_layers[1]
    assert calls[4][1] == poi_layers[0]
    assert calls[5] == ("save", "result.svg")


def test_create_map_defaults_to_empty_layers(
    pbf_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class SpyMapper:
        def __init__(
            self,
            pbf_path: str,
            scale: int = 100000,
            dpi: int = 300,
            bounds: tuple[float, float, float, float] | None = None,
            background_color: str | None = None,
        ):
            del pbf_path, scale, dpi, bounds, background_color

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: ANN001
            return None

        def render_features(
            self, feature_spec: FeatureSpec, style: Style, _progress_bar=None
        ) -> None:
            del feature_spec, style
            calls.append("render_features")

        def place_poi_markers(
            self,
            coords: list[tuple[float, float]],
            poi_style: PoiStyle,
            _progress_bar=None,
        ) -> None:
            del coords, poi_style
            calls.append("place_poi_markers")

        def save(self, output_path: str) -> None:
            del output_path
            calls.append("save")

    monkeypatch.setattr(create_map_module, "SvgMapper", SpyMapper)

    create_map(pbf_path=str(pbf_path), output_path="empty.svg")

    assert calls == ["save"]


def test_create_map_show_progress_updates_and_closes_bar(
    pbf_path: Path,
    marker_svg_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []
    created_bars: list[ProgressSpy] = []

    class FakeTqdm(ProgressSpy):
        def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
            super().__init__()
            self.args = args
            self.kwargs = kwargs
            self.updates: list[int] = []
            self.closed = False
            created_bars.append(self)

        def update(self, value: int) -> None:
            self.updates.append(value)

        def close(self) -> None:
            self.closed = True

    class SpyMapper:
        def __init__(self, **kwargs):  # noqa: ANN003
            calls.append(("init", kwargs))

        def __enter__(self):
            calls.append(("enter", None))
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: ANN001
            calls.append(("exit", None))
            return None

        def render_features(
            self, feature_spec: FeatureSpec, style: Style, _progress_bar=None
        ) -> None:
            calls.append(("render_features", (feature_spec, style, _progress_bar)))

        def place_poi_markers(
            self,
            coords: list[tuple[float, float]],
            poi_style: PoiStyle,
            _progress_bar=None,
        ) -> None:
            calls.append(("place_poi_markers", (coords, poi_style, _progress_bar)))

        def save(self, output_path: str) -> None:
            calls.append(("save", output_path))

    monkeypatch.setattr(create_map_module, "SvgMapper", SpyMapper)
    monkeypatch.setattr(create_map_module, "tqdm", FakeTqdm)

    create_map(
        pbf_path=str(pbf_path),
        feature_layers=[(features.ROADS.MAJOR, Style(stroke="#000000"))],
        poi_layers=[
            (
                [(52.0, 8.0)],
                PoiStyle(marker_svg_path=str(marker_svg_path), scale=1.0),
            )
        ],
        output_path="progress.svg",
        show_progress=True,
    )

    assert len(created_bars) == 1
    progress_bar = created_bars[0]
    assert progress_bar.kwargs["desc"] == "Rendering map"
    assert progress_bar.updates == [1, 1]
    assert progress_bar.descriptions == ["Layer 1/2", "Layer 2/2"]
    assert progress_bar.closed is True
    assert calls[2][0] == "render_features"
    assert calls[2][1][2] is None
    assert calls[3][0] == "place_poi_markers"
    assert calls[3][1][2] is None


def test_svgmapper_render_features_updates_progress_bar(
    pbf_path: Path,
    patched_svgmapper_dependencies,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def spy_render_features(self, features, style, layer_id, _progress_bar=None):  # noqa: ANN001
        captured["features"] = features
        captured["style"] = style
        captured["layer_id"] = layer_id
        captured["progress_bar"] = _progress_bar
        return ET.Element("svg")

    monkeypatch.setattr(DummyRenderer, "render_features", spy_render_features)
    progress = ProgressSpy()

    with SvgMapper(str(pbf_path)) as mapper:
        mapper.render_features(
            features.ROADS.MAJOR,
            Style(stroke="#000"),
            _progress_bar=progress,
        )

    assert progress.descriptions == ["Parsing PBF...", "Rendering features"]
    assert progress.n == 0
    assert progress.total == 0
    assert progress.refresh_calls == 2
    assert captured["layer_id"] == "0 highway"
    assert captured["progress_bar"] is progress


def test_svgmapper_place_poi_updates_progress_bar(
    pbf_path: Path,
    marker_svg_path: Path,
    patched_svgmapper_dependencies,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def spy_place_poi_markers(
        self,
        coords,
        poi_style,
        layer_id="pois",
        _progress_bar=None,
    ):  # noqa: ANN001
        captured["coords"] = coords
        captured["poi_style"] = poi_style
        captured["layer_id"] = layer_id
        captured["progress_bar"] = _progress_bar
        return ET.Element("svg")

    monkeypatch.setattr(DummyRenderer, "place_poi_markers", spy_place_poi_markers)
    progress = ProgressSpy()
    coords = [(52.0, 8.0), (52.1, 8.1)]

    with SvgMapper(str(pbf_path)) as mapper:
        mapper.place_poi_markers(
            coords=coords,
            poi_style=PoiStyle(marker_svg_path=str(marker_svg_path), scale=1.0),
            _progress_bar=progress,
        )

    assert progress.descriptions == ["Placing markers"]
    assert progress.n == 0
    assert progress.total == len(coords)
    assert progress.refresh_calls == 1
    assert captured["layer_id"] == "0 pois"
    assert captured["progress_bar"] is progress
