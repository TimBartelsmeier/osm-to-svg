import httpx
import pytest

from osm_to_svg.geocoding import get_bbox_from_place


class DummyResponse:
    def __init__(self, payload, raise_error: Exception | None = None):  # noqa: ANN001
        self._payload = payload
        self._raise_error = raise_error

    def raise_for_status(self) -> None:
        if self._raise_error:
            raise self._raise_error

    def json(self):  # noqa: ANN201
        return self._payload


def test_get_bbox_from_place_rejects_conflicting_width_params() -> None:
    with pytest.raises(ValueError, match="Cannot specify both width_km"):
        get_bbox_from_place("Hannover", width_km=10, east_km=5, west_km=5, height_km=8)


def test_get_bbox_from_place_rejects_conflicting_height_params() -> None:
    with pytest.raises(ValueError, match="Cannot specify both height_km"):
        get_bbox_from_place(
            "Hannover",
            width_km=10,
            height_km=8,
            north_km=4,
            south_km=4,
        )


def test_get_bbox_from_place_rejects_missing_dimension_pairs() -> None:
    with pytest.raises(ValueError, match="Must specify either width_km"):
        get_bbox_from_place("Hannover", north_km=5, south_km=5)

    with pytest.raises(ValueError, match="Must specify either height_km"):
        get_bbox_from_place("Hannover", east_km=5, west_km=5)


def test_get_bbox_from_place_computes_bbox_from_mocked_geocode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url, params, headers, timeout):  # noqa: ANN001, ANN202
        assert "nominatim" in url
        assert params["q"] == "Hannover"
        assert timeout == 30
        return DummyResponse([{"lat": "52.5", "lon": "9.7"}])

    monkeypatch.setattr(httpx, "get", fake_get)

    min_lon, min_lat, max_lon, max_lat = get_bbox_from_place(
        "Hannover",
        width_km=10,
        height_km=20,
    )

    assert min_lon < max_lon
    assert min_lat < max_lat
    assert min_lon == pytest.approx(9.6254, rel=1e-3)
    assert max_lon == pytest.approx(9.7746, rel=1e-3)


def test_get_bbox_from_place_wraps_http_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url, params, headers, timeout):  # noqa: ANN001, ANN202
        raise httpx.ConnectError("network down")

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(httpx.HTTPError, match="Failed to geocode"):
        get_bbox_from_place("Hannover", width_km=10, height_km=10)


def test_get_bbox_from_place_raises_when_no_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: DummyResponse([]))

    with pytest.raises(ValueError, match="Could not find location"):
        get_bbox_from_place("Nowhere", width_km=10, height_km=10)
