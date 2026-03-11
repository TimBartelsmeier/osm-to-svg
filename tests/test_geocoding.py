import httpx
import pytest

from osm_to_svg.acquisition.geocoding import geocode_place


class DummyResponse:
    def __init__(self, payload, raise_error: Exception | None = None):  # noqa: ANN001
        self._payload = payload
        self._raise_error = raise_error

    def raise_for_status(self) -> None:
        if self._raise_error:
            raise self._raise_error

    def json(self):  # noqa: ANN201
        return self._payload


def test_geocode_place_returns_lat_lon(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url, params, headers, timeout):  # noqa: ANN001, ANN202
        assert "nominatim" in url
        assert params["q"] == "Hannover, Germany"
        assert timeout == 30
        return DummyResponse([{"lat": "52.3759", "lon": "9.7320"}])

    monkeypatch.setattr(httpx, "get", fake_get)

    lat, lon = geocode_place("Hannover, Germany")

    assert lat == pytest.approx(52.3759)
    assert lon == pytest.approx(9.7320)


def test_geocode_place_forwards_custom_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_get(url, params, headers, timeout):  # noqa: ANN001, ANN202
        captured["timeout"] = timeout
        return DummyResponse([{"lat": "52.0", "lon": "9.0"}])

    monkeypatch.setattr(httpx, "get", fake_get)

    geocode_place("Hannover", timeout=60)

    assert captured["timeout"] == 60


def test_geocode_place_wraps_http_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url, params, headers, timeout):  # noqa: ANN001, ANN202
        raise httpx.ConnectError("network down")

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(httpx.HTTPError, match="Failed to geocode"):
        geocode_place("Hannover")


def test_geocode_place_raises_for_status_on_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: DummyResponse(
            [], raise_error=httpx.HTTPStatusError("404", request=None, response=None)
        ),
    )

    with pytest.raises(httpx.HTTPError, match="Failed to geocode"):
        geocode_place("Hannover")


def test_geocode_place_raises_when_no_results(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: DummyResponse([]))

    with pytest.raises(ValueError, match="Could not find location"):
        geocode_place("Nowhere Really Obscure Place Name XYZ")


def test_geocode_place_uses_first_result(monkeypatch: pytest.MonkeyPatch) -> None:
    """When Nominatim returns multiple results, geocode_place uses the first one."""
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: DummyResponse(
            [{"lat": "1.0", "lon": "2.0"}, {"lat": "3.0", "lon": "4.0"}]
        ),
    )

    lat, lon = geocode_place("Ambiguous Place")

    assert lat == pytest.approx(1.0)
    assert lon == pytest.approx(2.0)
