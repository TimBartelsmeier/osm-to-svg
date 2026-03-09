import pytest

from osm_to_svg.projection import CoordinateTransformer


@pytest.fixture
def transformer() -> CoordinateTransformer:
    return CoordinateTransformer((8.0, 52.0, 8.2, 52.2), scale=10000, dpi=96)


def test_projection_dimensions_are_positive(transformer: CoordinateTransformer) -> None:
    width, height = transformer.get_dimensions()
    assert width > 0
    assert height > 0


def test_projection_bounds_map_to_svg_frame(transformer: CoordinateTransformer) -> None:
    min_lon, min_lat, max_lon, max_lat = transformer.geo_bounds
    width, height = transformer.get_dimensions()

    x_min, y_bottom = transformer.latlon_to_svg(min_lat, min_lon)
    x_max, y_top = transformer.latlon_to_svg(max_lat, max_lon)

    assert x_min == pytest.approx(0.0, abs=1e-6)
    assert x_max == pytest.approx(width, abs=1e-6)
    assert y_top == pytest.approx(0.0, abs=1e-6)
    assert y_bottom == pytest.approx(height, abs=1e-6)


def test_projection_viewbox_matches_dimensions(
    transformer: CoordinateTransformer,
) -> None:
    width, height = transformer.get_dimensions()
    assert transformer.get_viewbox() == f"0 0 {width} {height}"


def test_projection_meters_to_pixels_returns_positive_scalars(
    transformer: CoordinateTransformer,
) -> None:
    px_x, px_y = transformer.meters_to_pixels()
    assert px_x > 0
    assert px_y > 0


def test_projection_rejects_invalid_scale_and_dpi() -> None:
    with pytest.raises(ValueError, match="scale must be greater than 0"):
        CoordinateTransformer((8.0, 52.0, 8.2, 52.2), scale=0, dpi=96)

    with pytest.raises(ValueError, match="dpi must be greater than 0"):
        CoordinateTransformer((8.0, 52.0, 8.2, 52.2), scale=10000, dpi=0)


def test_projection_rejects_invalid_bounds() -> None:
    with pytest.raises(ValueError, match="min_lon"):
        CoordinateTransformer((8.2, 52.0, 8.0, 52.2), scale=10000, dpi=96)
