from osm_to_svg import features
from osm_to_svg.features import FeatureSpec

# ---------------------------------------------------------------------------
# FeatureSpec construction
# ---------------------------------------------------------------------------


def test_feature_spec_has_correct_tag_filters_for_road() -> None:
    assert features.ROADS.MOTORWAY.tag_filters == {"highway": ["motorway"]}
    assert features.ROADS.MOTORWAY.needs_areas is False


def test_feature_spec_has_correct_tag_filters_for_railway() -> None:
    assert features.RAILWAYS.RAIL.tag_filters == {"railway": ["rail"]}
    assert features.RAILWAYS.RAIL.needs_areas is False


def test_feature_spec_has_correct_tag_filters_for_linear_waterway() -> None:
    assert features.WATER.RIVER.tag_filters == {"waterway": ["river"]}
    assert features.WATER.RIVER.needs_areas is False


def test_feature_spec_water_body_uses_natural_tag_and_needs_areas() -> None:
    assert features.WATER.WATER.tag_filters == {"natural": ["water"]}
    assert features.WATER.WATER.needs_areas is True


def test_feature_spec_building_uses_building_tag_and_needs_areas() -> None:
    assert features.BUILDINGS.HOUSE.tag_filters == {"building": ["house"]}
    assert features.BUILDINGS.HOUSE.needs_areas is True


def test_feature_spec_green_space_splits_by_tag_key() -> None:
    assert features.GREEN_SPACES.PARK.tag_filters == {"leisure": ["park"]}
    assert features.GREEN_SPACES.WOOD.tag_filters == {"natural": ["wood"]}
    assert features.GREEN_SPACES.FOREST.tag_filters == {"landuse": ["forest"]}
    assert features.GREEN_SPACES.PARK.needs_areas is True


# ---------------------------------------------------------------------------
# Shorthands
# ---------------------------------------------------------------------------


def test_roads_major_shorthand_contains_expected_values() -> None:
    assert "motorway" in features.ROADS.MAJOR.tag_filters["highway"]
    assert "tertiary" in features.ROADS.MAJOR.tag_filters["highway"]
    assert features.ROADS.MAJOR.needs_areas is False


def test_railways_active_shorthand_covers_all_active_types() -> None:
    values = features.RAILWAYS.ACTIVE.tag_filters["railway"]
    assert "rail" in values
    assert "tram" in values
    assert "abandoned" not in values


def test_waterways_bodies_shorthand_uses_natural_water_and_needs_areas() -> None:
    assert features.WATER.BODIES.tag_filters == {"natural": ["water"]}
    assert features.WATER.BODIES.needs_areas is True


def test_waterways_linear_shorthand_does_not_need_areas() -> None:
    assert features.WATER.LINEAR.needs_areas is False


def test_buildings_residential_shorthand_covers_subtypes() -> None:
    values = features.BUILDINGS.RESIDENTIAL.tag_filters["building"]
    assert "house" in values
    assert "apartments" in values
    assert features.BUILDINGS.RESIDENTIAL.needs_areas is True


def test_green_spaces_all_shorthand_covers_all_tag_keys() -> None:
    assert "leisure" in features.GREEN_SPACES.ALL.tag_filters
    assert "natural" in features.GREEN_SPACES.ALL.tag_filters
    assert "landuse" in features.GREEN_SPACES.ALL.tag_filters


# ---------------------------------------------------------------------------
# FeatureSpec | union operator
# ---------------------------------------------------------------------------


def test_or_merges_tag_filters_from_two_specs() -> None:
    combined = features.ROADS.MOTORWAY | features.ROADS.PRIMARY
    assert "motorway" in combined.tag_filters["highway"]
    assert "primary" in combined.tag_filters["highway"]


def test_or_merges_different_tag_keys() -> None:
    combined = features.ROADS.MAJOR | features.WATER.BODIES
    assert "highway" in combined.tag_filters
    assert "natural" in combined.tag_filters


def test_or_needs_areas_is_true_if_any_spec_needs_areas() -> None:
    combined = features.ROADS.MAJOR | features.WATER.BODIES  # roads=False, bodies=True
    assert combined.needs_areas is True


def test_or_needs_areas_is_false_when_neither_spec_needs_areas() -> None:
    combined = features.ROADS.MAJOR | features.RAILWAYS.ACTIVE
    assert combined.needs_areas is False


def test_or_deduplicates_values_within_same_key() -> None:
    # ROADS.MAJOR already contains motorway; combining with ROADS.MOTORWAY should not duplicate
    combined = features.ROADS.MAJOR | features.ROADS.MOTORWAY
    assert combined.tag_filters["highway"].count("motorway") == 1


# ---------------------------------------------------------------------------
# Name collision resolution (_TYPE suffix)
# ---------------------------------------------------------------------------


def test_pedestrian_type_is_single_value() -> None:
    assert features.ROADS.PEDESTRIAN_TYPE.tag_filters == {"highway": ["pedestrian"]}


def test_pedestrian_shorthand_covers_multiple_values() -> None:
    values = features.ROADS.PEDESTRIAN.tag_filters["highway"]
    assert "footway" in values
    assert "pedestrian" in values
    assert "steps" in values


def test_buildings_residential_type_is_single_value() -> None:
    assert features.BUILDINGS.RESIDENTIAL_TYPE.tag_filters == {
        "building": ["residential"]
    }


def test_buildings_commercial_type_is_single_value() -> None:
    assert features.BUILDINGS.COMMERCIAL_TYPE.tag_filters == {
        "building": ["commercial"]
    }


def test_buildings_industrial_type_is_single_value() -> None:
    assert features.BUILDINGS.INDUSTRIAL_TYPE.tag_filters == {
        "building": ["industrial"]
    }
