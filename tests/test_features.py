from enum import Enum

import pytest

from osm_to_svg.features import (
    GreenSpaceType,
    RailwayType,
    RoadType,
    WaterwayType,
    get_osm_filter,
)


def test_get_osm_filter_for_regular_feature_uses_tag_mapping() -> None:
    result = get_osm_filter(RoadType, [RoadType.MOTORWAY, RoadType.PRIMARY])
    assert result == {"highway": ["motorway", "primary"]}


def test_get_osm_filter_for_waterways_returns_multi_tag_filter() -> None:
    result = get_osm_filter(WaterwayType, [WaterwayType.RIVER])
    assert result["waterway"] == ["river"]
    assert result["natural"] == ["water", "coastline"]


def test_get_osm_filter_for_waterways_without_subtypes_uses_defaults() -> None:
    result = get_osm_filter(WaterwayType)
    assert result["waterway"] == ["river", "stream", "canal", "drain", "ditch"]
    assert result["natural"] == ["water", "coastline"]


def test_get_osm_filter_for_green_spaces_splits_by_tag_key() -> None:
    result = get_osm_filter(
        GreenSpaceType,
        [GreenSpaceType.PARK, GreenSpaceType.WOOD, GreenSpaceType.MEADOW],
    )
    assert result == {
        "leisure": ["park"],
        "natural": ["wood"],
        "landuse": ["meadow"],
    }


def test_get_osm_filter_for_green_spaces_without_subtypes_uses_all_groups() -> None:
    result = get_osm_filter(GreenSpaceType)
    assert "leisure" in result
    assert "natural" in result
    assert "landuse" in result


def test_get_osm_filter_for_regular_feature_without_subtypes_returns_all() -> None:
    result = get_osm_filter(RailwayType)
    assert set(result.keys()) == {"railway"}
    assert len(result["railway"]) == len(list(RailwayType))


def test_get_osm_filter_raises_for_unknown_feature_type() -> None:
    class UnknownFeature(str, Enum):
        VALUE = "value"

    with pytest.raises(ValueError, match="Unknown feature type"):
        get_osm_filter(UnknownFeature)
