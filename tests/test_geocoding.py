import httpx
import pytest

from osm_to_svg.acquisition.geocoding import (
    geocode_coordinates,
    geocode_osm_object,
    get_polygon_from_osm_id,
)
from osm_to_svg.models import OsmObjectId


class DummyResponse:
    def __init__(self, payload, raise_error: Exception | None = None):
        self._payload = payload
        self._raise_error = raise_error

    def raise_for_status(self) -> None:
        if self._raise_error:
            raise self._raise_error

    def json(self):
        return self._payload


def test_geocode_place_returns_lat_lon(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url, params, headers, timeout):
        assert "nominatim" in url
        assert params["q"] == "Hannover, Germany"
        assert timeout == 30
        return DummyResponse([{"lat": "52.3759", "lon": "9.7320"}])

    monkeypatch.setattr(httpx, "get", fake_get)

    lat, lon = geocode_coordinates("Hannover, Germany")

    assert lat == pytest.approx(52.3759)
    assert lon == pytest.approx(9.7320)


def test_geocode_osm_object_returns_typed_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: DummyResponse(
            [{"lat": "52.0", "lon": "9.0", "osm_type": "relation", "osm_id": 123}]
        ),
    )

    assert geocode_osm_object("Herrenhaeuser Gaerten") == OsmObjectId("relation", 123)


def test_geocode_osm_object_rejects_missing_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: DummyResponse([{"lat": "52.0", "lon": "9.0"}]),
    )

    with pytest.raises(ValueError, match="no valid OSM object identity"):
        geocode_osm_object("Unknown object")


def test_geocode_osm_object_rejects_non_numeric_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: DummyResponse(
            [{"osm_type": "way", "osm_id": "not-a-number"}]
        ),
    )

    with pytest.raises(ValueError, match="no valid OSM object identity"):
        geocode_osm_object("Invalid object")


def test_geocode_place_forwards_custom_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_get(url, params, headers, timeout):
        captured["timeout"] = timeout
        return DummyResponse([{"lat": "52.0", "lon": "9.0"}])

    monkeypatch.setattr(httpx, "get", fake_get)

    geocode_coordinates("Hannover", timeout=60)

    assert captured["timeout"] == 60


def test_geocode_place_wraps_http_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url, params, headers, timeout):
        raise httpx.ConnectError("network down")

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(httpx.HTTPError, match="Failed to geocode"):
        geocode_coordinates("Hannover")


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
        geocode_coordinates("Hannover")


def test_geocode_place_raises_when_no_results(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: DummyResponse([]))

    with pytest.raises(ValueError, match="Could not find location"):
        geocode_coordinates("Nowhere Really Obscure Place Name XYZ")


def test_geocode_place_uses_first_result(monkeypatch: pytest.MonkeyPatch) -> None:
    """When Nominatim returns multiple results, geocode_place uses the first one."""
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: DummyResponse(
            [{"lat": "1.0", "lon": "2.0"}, {"lat": "3.0", "lon": "4.0"}]
        ),
    )

    lat, lon = geocode_coordinates("Ambiguous Place")

    assert lat == pytest.approx(1.0)
    assert lon == pytest.approx(2.0)


def test_get_polygon_from_osm_id_converts_geojson_coordinates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_get(url, params, headers, timeout):
        captured.update(params)
        return DummyResponse(
            {
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[8.0, 52.0], [8.1, 52.0], [8.1, 52.1], [8.0, 52.0]]
                    ],
                }
            }
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    polygon = get_polygon_from_osm_id(OsmObjectId("relation", 123), timeout=60)

    assert captured == {
        "osmtype": "R",
        "osmid": 123,
        "format": "json",
        "polygon_geojson": 1,
    }
    assert polygon == (
        (52.0, 8.0),
        (52.0, 8.1),
        (52.1, 8.1),
        (52.0, 8.0),
    )


@pytest.mark.parametrize("geometry_type", ["Point", "LineString", "MultiPolygon"])
def test_get_polygon_from_osm_id_rejects_unsupported_geometry(
    monkeypatch: pytest.MonkeyPatch,
    geometry_type: str,
) -> None:
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: DummyResponse(
            {"geometry": {"type": geometry_type, "coordinates": []}}
        ),
    )

    with pytest.raises(ValueError, match="does not have a supported polygon"):
        get_polygon_from_osm_id(OsmObjectId("way", 123))


def test_get_polygon_from_osm_id_rejects_holes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: DummyResponse(
            {
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[8.0, 52.0], [8.1, 52.0], [8.0, 52.1], [8.0, 52.0]],
                        [[8.02, 52.02], [8.03, 52.02], [8.02, 52.03], [8.02, 52.02]],
                    ],
                }
            }
        ),
    )

    with pytest.raises(ValueError, match="holes"):
        get_polygon_from_osm_id(OsmObjectId("way", 123))


@pytest.mark.parametrize(
    ("coordinates", "error", "message"),
    [
        ("invalid", TypeError, "invalid polygon coordinates"),
        ([[8.0]], ValueError, "invalid polygon coordinates"),
        (
            [[8.0, 52.0], [8.1, 52.1], [8.0, 52.1], [8.1, 52.0]],
            ValueError,
            "invalid polygon geometry",
        ),
    ],
)
def test_get_polygon_from_osm_id_rejects_invalid_ring_data(
    monkeypatch: pytest.MonkeyPatch,
    coordinates,
    error: type[Exception],
    message: str,
) -> None:
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: DummyResponse(
            {"geometry": {"type": "Polygon", "coordinates": [coordinates]}}
        ),
    )

    with pytest.raises(error, match=message):
        get_polygon_from_osm_id(OsmObjectId("way", 123))


def test_get_polygon_from_osm_id_wraps_http_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_get(*args, **kwargs):
        raise httpx.ConnectError("network down")

    monkeypatch.setattr(httpx, "get", fail_get)

    with pytest.raises(httpx.HTTPError, match="Failed to get polygon"):
        get_polygon_from_osm_id(OsmObjectId("relation", 123))
