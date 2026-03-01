from pathlib import Path

import pytest


class DummyTransformer:
    def get_dimensions(self) -> tuple[int, int]:
        return (200, 100)

    def get_viewbox(self) -> str:
        return "0 0 200 100"

    def latlon_to_svg(self, lat: float, lon: float) -> tuple[float, float]:
        return (100.0 + lon * 10.0, 50.0 - lat * 10.0)

    def meters_to_pixels(self) -> tuple[float, float]:
        return (2.0, 4.0)


@pytest.fixture
def dummy_transformer() -> DummyTransformer:
    return DummyTransformer()


@pytest.fixture
def marker_svg_path(tmp_path: Path) -> Path:
    marker = tmp_path / "marker.svg"
    marker.write_text(
        """
<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"10\" height=\"20\" viewBox=\"0 0 10 20\">
  <rect x=\"0\" y=\"0\" width=\"10\" height=\"20\" fill=\"#ff0000\"/>
</svg>
""".strip(),
        encoding="utf-8",
    )
    return marker
