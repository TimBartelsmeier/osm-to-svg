from pathlib import Path

import pytest

from osm_to_svg import features
from osm_to_svg.features import FeatureSpec
from osm_to_svg.parser import FeatureHandler, PBFParser


@pytest.fixture
def tiny_pbf_fixture_path() -> Path:
    fixture = Path(__file__).parent / "fixtures" / "tiny.osm.pbf"
    if not fixture.exists():
        pytest.skip("tiny.osm.pbf fixture not generated yet")
    return fixture


def test_parser_get_bounds_from_tiny_fixture(tiny_pbf_fixture_path: Path) -> None:
    parser = PBFParser(str(tiny_pbf_fixture_path))

    min_lon, min_lat, max_lon, max_lat = parser.get_bounds()

    assert min_lon == pytest.approx(8.0)
    assert min_lat == pytest.approx(52.0)
    assert max_lon == pytest.approx(8.02)
    assert max_lat == pytest.approx(52.015)


def test_parser_extracts_road_features(tiny_pbf_fixture_path: Path) -> None:
    parser = PBFParser(str(tiny_pbf_fixture_path))

    roads = parser.extract_features(features.ROADS.PRIMARY)

    assert len(roads) == 1
    assert roads[0].tags["highway"] == "primary"
    assert roads[0].is_closed is False


def test_parser_extracts_buildings_without_duplicate_ids(
    tiny_pbf_fixture_path: Path,
) -> None:
    parser = PBFParser(str(tiny_pbf_fixture_path))

    buildings = parser.extract_features(features.BUILDINGS.YES)

    assert len(buildings) >= 1
    assert all(feature.tags.get("building") == "yes" for feature in buildings)

    ids = [feature.tags.get("id") for feature in buildings if "id" in feature.tags]
    if ids:
        assert len(ids) == len(set(ids))


def test_parser_extracts_waterway_features(tiny_pbf_fixture_path: Path) -> None:
    parser = PBFParser(str(tiny_pbf_fixture_path))

    waterways = parser.extract_features(features.WATER.RIVER)

    assert len(waterways) == 1
    assert waterways[0].tags["waterway"] == "river"


def test_feature_handler_matches_water_body_via_natural_tag() -> None:
    # WATERWAYS.BODIES carries natural=water in its tag_filters directly
    handler = FeatureHandler(features.WATER.BODIES)

    assert handler._matches_filter({"natural": "water"}) is True
    assert handler._matches_filter({"waterway": "river"}) is False


def test_feature_handler_area_extraction_and_error_handling() -> None:
    class DummyNode:
        def __init__(self, lon: float, lat: float):
            self.lon = lon
            self.lat = lat

    class DummyArea:
        def __init__(self, tags: dict[str, str], rings):
            self.tags = [type("Tag", (), {"k": k, "v": v}) for k, v in tags.items()]
            self._rings = rings

        def outer_rings(self):
            if isinstance(self._rings, Exception):
                raise self._rings
            return self._rings

    handler = FeatureHandler(features.BUILDINGS.YES)

    valid_area = DummyArea(
        {"building": "yes"},
        [
            [
                DummyNode(8.0, 52.0),
                DummyNode(8.01, 52.0),
                DummyNode(8.01, 52.01),
                DummyNode(8.0, 52.0),
            ]
        ],
    )
    handler.area(valid_area)
    assert len(handler.features) == 1
    assert handler.features[0].is_closed is True

    handler.area(DummyArea({"building": "yes"}, []))
    handler.area(DummyArea({"building": "yes"}, RuntimeError("bad geometry")))


def test_feature_handler_way_skips_invalid_geometry() -> None:
    class DummyWayNode:
        def __init__(self, ref: int):
            self.ref = ref

    class DummyWay:
        def __init__(self):
            self.tags = [type("Tag", (), {"k": "highway", "v": "primary"})]
            self.nodes = [DummyWayNode(1)]

    handler = FeatureHandler(features.ROADS.PRIMARY)
    handler.node_cache = {1: (8.0, 52.0)}

    handler.way(DummyWay())
    assert handler.features == []


def test_feature_handler_does_not_match_unrelated_tags() -> None:
    handler = FeatureHandler(features.WATER.RIVER)

    assert handler._matches_filter({"natural": "water"}) is False
    assert handler._matches_filter({"natural": "coastline"}) is False
    assert handler._matches_filter({"waterway": "river"}) is True
