import pytest

from osm_to_svg.acquisition.bbox import get_bbox_around_coordinates

# ---------------------------------------------------------------------------
# Argument validation
# ---------------------------------------------------------------------------


def test_rejects_conflicting_width_params() -> None:
    with pytest.raises(ValueError, match="Cannot specify both width_km"):
        get_bbox_around_coordinates(
            52.5, 9.7, width_km=10, east_km=5, west_km=5, height_km=8
        )


def test_rejects_conflicting_height_params() -> None:
    with pytest.raises(ValueError, match="Cannot specify both height_km"):
        get_bbox_around_coordinates(
            52.5,
            9.7,
            width_km=10,
            height_km=8,
            north_km=4,
            south_km=4,
        )


def test_rejects_missing_horizontal_dimension() -> None:
    with pytest.raises(ValueError, match="Must specify either width_km"):
        get_bbox_around_coordinates(52.5, 9.7, north_km=5, south_km=5)


def test_rejects_missing_vertical_dimension() -> None:
    with pytest.raises(ValueError, match="Must specify either height_km"):
        get_bbox_around_coordinates(52.5, 9.7, east_km=5, west_km=5)


def test_rejects_only_one_of_east_west() -> None:
    with pytest.raises(ValueError, match="Must specify either width_km"):
        get_bbox_around_coordinates(52.5, 9.7, east_km=5, height_km=10)


def test_rejects_only_one_of_north_south() -> None:
    with pytest.raises(ValueError, match="Must specify either height_km"):
        get_bbox_around_coordinates(52.5, 9.7, width_km=10, north_km=5)


def test_rejects_zero_width_km() -> None:
    with pytest.raises(ValueError, match="width_km must be greater than 0"):
        get_bbox_around_coordinates(52.5, 9.7, width_km=0, height_km=10)


def test_rejects_negative_height_km() -> None:
    with pytest.raises(ValueError, match="height_km must be greater than 0"):
        get_bbox_around_coordinates(52.5, 9.7, width_km=10, height_km=-5)


def test_rejects_zero_east_km() -> None:
    with pytest.raises(ValueError, match="east_km must be greater than 0"):
        get_bbox_around_coordinates(
            52.5, 9.7, east_km=0, west_km=5, north_km=5, south_km=5
        )


def test_rejects_negative_north_km() -> None:
    with pytest.raises(ValueError, match="north_km must be greater than 0"):
        get_bbox_around_coordinates(
            52.5, 9.7, east_km=5, west_km=5, north_km=-1, south_km=5
        )


# ---------------------------------------------------------------------------
# Correct bbox computation
# ---------------------------------------------------------------------------


def test_symmetric_bbox_is_centred_on_coordinates() -> None:
    lat, lon = 52.5, 9.7
    south_lat, west_lon, north_lat, east_lon = get_bbox_around_coordinates(
        lat, lon, width_km=10, height_km=20
    )

    centre_lat = (south_lat + north_lat) / 2
    centre_lon = (west_lon + east_lon) / 2

    assert centre_lat == pytest.approx(lat, abs=1e-9)
    assert centre_lon == pytest.approx(lon, abs=1e-9)


def test_symmetric_bbox_lon_approx_values() -> None:
    """Check computed lon offsets for a well-known latitude."""
    # At lat=52.5, lon_degree_km = 111.0 * cos(52.5°) ≈ 67.55 km/deg
    # width_km=10 → half = 5 km → offset = 5 / 67.55 ≈ 0.07402 deg
    import math

    lon_deg_km = 111.0 * math.cos(math.radians(52.5))
    expected_min_lon = 9.7 - 5 / lon_deg_km
    expected_max_lon = 9.7 + 5 / lon_deg_km

    _south_lat, west_lon, _north_lat, east_lon = get_bbox_around_coordinates(
        52.5, 9.7, width_km=10, height_km=20
    )

    assert west_lon == pytest.approx(expected_min_lon, rel=1e-6)
    assert east_lon == pytest.approx(expected_max_lon, rel=1e-6)


def test_symmetric_bbox_lat_approx_values() -> None:
    """Check computed lat offsets (invariant of longitude)."""
    # height_km=20 → half = 10 km → offset = 10/111 ≈ 0.09009
    south_lat, _west_lon, north_lat, _east_lon = get_bbox_around_coordinates(
        52.5, 9.7, width_km=10, height_km=20
    )

    assert south_lat == pytest.approx(52.5 - 10 / 111.0, rel=1e-4)
    assert north_lat == pytest.approx(52.5 + 10 / 111.0, rel=1e-4)


def test_asymmetric_bbox_east_west() -> None:
    """Asymmetric east/west offsets produce an off-centre bounding box."""
    lat, lon = 0.0, 0.0  # equator: lon_degree_km = 111 km/deg exactly
    _south_lat, west_lon, _north_lat, east_lon = get_bbox_around_coordinates(
        lat, lon, east_km=11.1, west_km=22.2, north_km=5, south_km=5
    )

    assert west_lon == pytest.approx(-22.2 / 111.0, rel=1e-4)
    assert east_lon == pytest.approx(11.1 / 111.0, rel=1e-4)


def test_asymmetric_bbox_north_south() -> None:
    """Asymmetric north/south offsets produce an off-centre bounding box."""
    lat, lon = 0.0, 0.0
    south_lat, _west_lon, north_lat, _east_lon = get_bbox_around_coordinates(
        lat, lon, width_km=10, north_km=33.3, south_km=11.1
    )

    assert south_lat == pytest.approx(-11.1 / 111.0, rel=1e-4)
    assert north_lat == pytest.approx(33.3 / 111.0, rel=1e-4)


def test_bbox_ordering() -> None:
    """south/west values are always less than north/east values."""
    south_lat, west_lon, north_lat, east_lon = get_bbox_around_coordinates(
        48.137, 11.576, width_km=15, height_km=10
    )

    assert west_lon < east_lon
    assert south_lat < north_lat


# ---------------------------------------------------------------------------
# Polar edge case
# ---------------------------------------------------------------------------


def test_raises_near_poles() -> None:
    with pytest.raises(ValueError, match="longitude degrees approach zero"):
        get_bbox_around_coordinates(90.0, 0.0, width_km=10, height_km=10)
