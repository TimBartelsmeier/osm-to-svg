from pathlib import Path

import pytest

from osm_to_svg import features
from osm_to_svg.features import FeatureSpec
from osm_to_svg.models import Feature, FeatureFilter, OsmObjectId
from osm_to_svg.parsing import BoundsHandler, FeatureHandler, FeatureQuery, PBFParser
from osm_to_svg.parsing.parser import _geometry_intersects_bbox, _segments_intersect


def test_geometry_intersects_bbox_includes_crossing_and_containment() -> None:
    bbox = ((52.0, 8.0), (52.0, 8.01), (52.01, 8.01), (52.01, 8.0))

    assert _geometry_intersects_bbox([(51.99, 8.005), (52.02, 8.005)], bbox)
    assert _geometry_intersects_bbox(
        [(51.9, 7.9), (51.9, 8.1), (52.1, 8.1), (52.1, 7.9), (51.9, 7.9)],
        bbox,
    )
    assert not _geometry_intersects_bbox([(51.9, 7.9), (51.9, 7.99)], bbox)


def test_geometry_intersects_bbox_rejects_disjoint_collinear_segment() -> None:
    bbox = ((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0))

    assert not _geometry_intersects_bbox([(0.0, 10.0), (0.0, 11.0)], bbox)


def test_geometry_intersects_concave_polygon_and_includes_boundary() -> None:
    polygon = (
        (52.0, 8.0),
        (52.0, 8.04),
        (52.04, 8.04),
        (52.02, 8.02),
        (52.04, 8.0),
    )

    assert _geometry_intersects_bbox([(52.01, 8.01), (52.01, 8.01)], polygon)
    assert _geometry_intersects_bbox([(52.0, 8.01), (51.99, 8.01)], polygon)
    assert not _geometry_intersects_bbox([(51.9, 7.9), (51.91, 7.91)], polygon)


def test_geometry_intersection_covers_open_and_containing_closed_paths() -> None:
    bbox = ((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0))

    assert not _geometry_intersects_bbox([(2.0, 2.0), (3.0, 3.0), (4.0, 4.0)], bbox)
    assert _geometry_intersects_bbox(
        [(-1.0, -1.0), (-1.0, 2.0), (2.0, 2.0), (2.0, -1.0), (-1.0, -1.0)],
        bbox,
    )


def test_geometry_intersection_covers_collinear_endpoint_case() -> None:
    bbox = ((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0))

    assert _geometry_intersects_bbox([(1.0, 0.0), (0.0, 0.0)], bbox)


@pytest.mark.parametrize(
    ("first", "second"),
    [
        (((0.0, 0.0), (0.0, 2.0)), ((0.0, 1.0), (1.0, 1.0))),
        (((0.0, 0.0), (0.0, 2.0)), ((1.0, 1.0), (0.0, 1.0))),
        (((0.0, 1.0), (1.0, 1.0)), ((0.0, 0.0), (0.0, 2.0))),
        (((1.0, 1.0), (0.0, 1.0)), ((0.0, 0.0), (0.0, 2.0))),
    ],
)
def test_segments_intersect_handles_each_collinear_endpoint_case(first, second) -> None:
    assert _segments_intersect(*first, *second)


def test_parser_limit_applies_include_and_exclude_areas() -> None:
    area = ((52.0, 8.0), (52.0, 8.01), (52.01, 8.01), (52.01, 8.0))
    feature = Feature(
        geometry=[(52.005, 8.005), (52.006, 8.006)],
        tags={"highway": "primary"},
    )

    assert PBFParser._matches_limit(feature, [area])
    assert not PBFParser._matches_limit(feature, [area], [area])


def test_parser_measurement_limits_are_inclusive() -> None:
    closed = Feature(
        geometry=[(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)],
        tags={},
        is_closed=True,
    )
    open_feature = Feature(
        geometry=[(0.0, 0.0), (0.0, 1.0)],
        tags={},
    )

    from osm_to_svg.parsing.parser import _GEOD

    area, _ = _GEOD.polygon_area_perimeter(
        [longitude for _, longitude in closed.geometry],
        [latitude for latitude, _ in closed.geometry],
    )
    length = _GEOD.line_length(
        [longitude for _, longitude in open_feature.geometry],
        [latitude for latitude, _ in open_feature.geometry],
    )

    assert PBFParser._matches_measurement_filter(
        closed,
        FeatureFilter(minimum_area=abs(area), maximum_area=abs(area)),
    )
    assert PBFParser._matches_measurement_filter(
        open_feature,
        FeatureFilter(minimum_length=length, maximum_length=length),
    )


def test_parser_measurement_limits_apply_only_to_matching_geometry_type() -> None:
    closed = Feature(
        geometry=[(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)],
        tags={},
        is_closed=True,
    )
    open_feature = Feature(
        geometry=[(0.0, 0.0), (0.0, 1.0)],
        tags={},
    )

    assert PBFParser._matches_measurement_filter(
        closed,
        FeatureFilter(minimum_length=10**12),
    )
    assert PBFParser._matches_measurement_filter(
        open_feature,
        FeatureFilter(minimum_area=10**12),
    )


def test_parser_limit_matches_any_of_multiple_areas() -> None:
    feature = Feature(
        geometry=[(53.0, 10.0), (53.01, 10.01)],
        tags={"highway": "primary"},
    )

    assert PBFParser._matches_limit(
        feature,
        [
            ((52.0, 8.0), (52.0, 8.01), (52.01, 8.01), (52.01, 8.0)),
            ((53.0, 10.0), (53.0, 10.01), (53.01, 10.01), (53.01, 10.0)),
        ],
        None,
    )


def test_parser_limit_matches_included_area() -> None:
    area = ((52.0, 8.0), (52.0, 8.01), (52.01, 8.01), (52.01, 8.0))
    area_feature = Feature(
        geometry=[(52.005, 8.005), (52.006, 8.006)],
        tags={"highway": "primary"},
    )
    assert PBFParser._matches_limit(area_feature, [area])


def test_parser_contains_requires_complete_feature_geometry() -> None:
    area = ((0.0, 0.0), (0.0, 2.0), (2.0, 2.0), (2.0, 0.0))

    assert PBFParser._matches_limit(
        Feature(geometry=[(0.5, 0.5), (1.5, 1.5)], tags={}),
        [area],
        area_match_mode="contains",
    )
    assert not PBFParser._matches_limit(
        Feature(geometry=[(-1.0, 1.0), (1.0, 1.0)], tags={}),
        [area],
        area_match_mode="contains",
    )


@pytest.fixture
def tiny_pbf_fixture_path() -> Path:
    fixture = Path(__file__).parent / "fixtures" / "tiny.osm.pbf"
    if not fixture.exists():
        pytest.skip("tiny.osm.pbf fixture not generated yet")
    return fixture


def test_parser_get_bounds_from_tiny_fixture(tiny_pbf_fixture_path: Path) -> None:
    parser = PBFParser(str(tiny_pbf_fixture_path))

    south_lat, west_lon, north_lat, east_lon = parser.get_bounds()

    assert south_lat == pytest.approx(52.0)
    assert west_lon == pytest.approx(8.0)
    assert north_lat == pytest.approx(52.015)
    assert east_lon == pytest.approx(8.02)


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

    waterways = parser.extract_features(features.WATERWAYS.RIVER)

    assert len(waterways) == 1
    assert waterways[0].tags["waterway"] == "river"


def test_parser_shared_queries_match_individual_extractions(
    tiny_pbf_fixture_path: Path,
) -> None:
    parser = PBFParser(str(tiny_pbf_fixture_path))
    queries = [
        FeatureQuery(features.ROADS.PRIMARY),
        FeatureQuery(features.WATERWAYS.RIVER),
        FeatureQuery(FeatureSpec(tag_filters={"building": ["yes"]})),
        FeatureQuery(features.BUILDINGS.YES),
    ]

    shared = parser.extract_features_for_queries(queries)
    individual = [parser.extract_features(query.spec) for query in queries]

    assert shared == individual


def test_parser_deduplicates_way_and_area_pass_for_same_object(monkeypatch) -> None:
    parser = PBFParser("unused.osm.pbf")
    way_feature = Feature(
        geometry=[(52.0, 8.0), (52.0, 8.01), (52.01, 8.01), (52.0, 8.0)],
        tags={"waterway": "riverbank"},
        is_closed=True,
        object_id=OsmObjectId("way", 42),
    )
    area_feature = Feature(
        geometry=[(52.0, 8.0), (52.0, 8.01), (52.01, 8.01), (52.0, 8.0)],
        tags=way_feature.tags,
        is_closed=True,
        object_id=way_feature.object_id,
    )

    class FakeHandler:
        instances = 0

        def __init__(self, spec):
            self.features = []
            self.spec = spec

        def apply_file(self, *args, **kwargs):
            FakeHandler.instances += 1
            self.features = [
                way_feature if FakeHandler.instances == 1 else area_feature
            ]

    monkeypatch.setattr("osm_to_svg.parsing.parser.FeatureHandler", FakeHandler)

    assert parser.extract_features(features.WATER_POLYGONS.RIVER) == [way_feature]


def test_feature_handler_matches_generic_water_polygon_via_natural_tag() -> None:
    handler = FeatureHandler(features.WATER_POLYGONS.WATER_AREA)

    assert handler._matches_filter({"natural": "water"}) is True
    assert handler._matches_filter({"waterway": "river"}) is False


def test_feature_handler_matches_water_polygon_with_all_required_tags() -> None:
    handler = FeatureHandler(features.WATER_POLYGONS.LAKE)

    assert handler._matches_filter({"natural": "water", "water": "lake"}) is True
    assert handler._matches_filter({"natural": "water", "water": "reservoir"}) is False
    assert handler._matches_filter({"natural": "water"}) is False


def test_feature_handler_matches_any_water_polygon_clause() -> None:
    handler = FeatureHandler(features.WATER_POLYGONS.RIVER)

    assert handler._matches_filter({"waterway": "riverbank"}) is True
    assert handler._matches_filter({"natural": "water", "water": "river"}) is True
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
    handler.area(
        DummyArea(
            {"building": "yes"},
            [[DummyNode(8.0, 52.0), DummyNode(8.01, 52.0), DummyNode(8.0, 52.01)]],
        )
    )
    handler.area(DummyArea({"building": "yes"}, RuntimeError("bad geometry")))


def test_feature_handler_preserves_all_outer_rings() -> None:
    class DummyNode:
        def __init__(self, lon: float, lat: float):
            self.lon = lon
            self.lat = lat

    class DummyArea:
        tags = [type("Tag", (), {"k": "building", "v": "yes"})]

        def outer_rings(self):
            return [
                [
                    DummyNode(8.0, 52.0),
                    DummyNode(8.01, 52.0),
                    DummyNode(8.01, 52.01),
                    DummyNode(8.0, 52.0),
                ],
                [
                    DummyNode(8.02, 52.0),
                    DummyNode(8.03, 52.0),
                    DummyNode(8.03, 52.01),
                    DummyNode(8.02, 52.0),
                ],
            ]

    handler = FeatureHandler(features.BUILDINGS.YES)
    handler.area(DummyArea())

    assert len(handler.features) == 2


def test_feature_handler_preserves_relation_holes_and_identity() -> None:
    class DummyNode:
        def __init__(self, lon: float, lat: float):
            self.lon = lon
            self.lat = lat

    class DummyArea:
        tags = [type("Tag", (), {"k": "natural", "v": "water"})]

        def from_way(self):
            return False

        def orig_id(self):
            return 2907930

        def outer_rings(self):
            return [
                [
                    DummyNode(8.0, 52.0),
                    DummyNode(8.1, 52.0),
                    DummyNode(8.1, 52.1),
                    DummyNode(8.0, 52.0),
                ]
            ]

        def inner_rings(self, outer_ring):
            return [
                [
                    DummyNode(8.02, 52.02),
                    DummyNode(8.08, 52.02),
                    DummyNode(8.08, 52.08),
                    DummyNode(8.02, 52.02),
                ]
            ]

    handler = FeatureHandler(features.WATER_POLYGONS.WATER_AREA)
    handler.area(DummyArea())

    assert len(handler.features) == 1
    feature = handler.features[0]
    assert feature.object_id == OsmObjectId("relation", 2907930)
    assert len(feature.inner_geometries) == 1


def test_bounds_handler_rejects_files_without_valid_nodes() -> None:
    with pytest.raises(ValueError, match="no valid node locations"):
        BoundsHandler().get_bounds()


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
    handler = FeatureHandler(features.WATERWAYS.RIVER)

    assert handler._matches_filter({"natural": "water"}) is False
    assert handler._matches_filter({"natural": "coastline"}) is False
    assert handler._matches_filter({"waterway": "river"}) is True
