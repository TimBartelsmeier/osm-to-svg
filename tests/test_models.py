from osm_to_svg.features import FeatureSpec
from osm_to_svg.models import FeatureFilter, FeatureLayer, OsmObjectId, Style


def test_osm_object_id_is_typed_and_stringifiable() -> None:
    object_id = OsmObjectId("relation", 123)

    assert str(object_id) == "relation/123"


def test_osm_object_id_rejects_non_positive_values() -> None:
    import pytest

    with pytest.raises(ValueError, match="greater than 0"):
        OsmObjectId("way", 0)


def test_feature_filter_normalizes_areas_and_limits() -> None:
    bbox = ((52.0, 9.0), (52.0, 9.1), (52.1, 9.1), (52.1, 9.0))
    feature_filter = FeatureFilter(
        areas=[bbox],
        minimum_area=0,
        maximum_area=1000,
        minimum_length=0,
        maximum_length=1000,
    )

    assert feature_filter.areas == ((*bbox, bbox[0]),)


def test_feature_filter_rejects_empty_areas() -> None:
    import pytest

    with pytest.raises(ValueError, match="areas must not be empty"):
        FeatureFilter(areas=[])
    with pytest.raises(ValueError, match="exclude_areas must not be empty"):
        FeatureFilter(exclude_areas=[])


def test_feature_filter_accepts_multiple_areas() -> None:
    first = ((52.0, 9.0), (52.0, 9.1), (52.1, 9.1), (52.1, 9.0))
    second = ((53.0, 10.0), (53.0, 10.1), (53.1, 10.1), (53.1, 10.0))
    feature_filter = FeatureFilter(areas=[first, second])

    assert feature_filter.areas == ((*first, first[0]), (*second, second[0]))


def test_feature_filter_accepts_include_and_exclude_areas() -> None:
    bbox = ((52.0, 9.0), (52.0, 9.1), (52.1, 9.1), (52.1, 9.0))
    feature_filter = FeatureFilter(
        areas=[bbox],
        exclude_areas=[bbox],
        area_match_mode="contains",
    )

    assert feature_filter.areas == ((*bbox, bbox[0]),)
    assert feature_filter.exclude_areas == ((*bbox, bbox[0]),)
    assert feature_filter.area_match_mode == "contains"


def test_feature_filter_rejects_unknown_area_match_mode() -> None:
    import pytest

    with pytest.raises(ValueError, match="area_match_mode"):
        FeatureFilter(
            area_match_mode="unknown",
        )


def test_feature_filter_rejects_invalid_metric_ranges() -> None:
    import pytest

    with pytest.raises(ValueError, match="minimum_area"):
        FeatureFilter(minimum_area=-1)
    with pytest.raises(ValueError, match="minimum_length"):
        FeatureFilter(minimum_length=-1)
    with pytest.raises(ValueError, match="must not exceed"):
        FeatureFilter(minimum_area=2, maximum_area=1)
    with pytest.raises(ValueError, match="must not exceed"):
        FeatureFilter(minimum_length=2, maximum_length=1)


def test_feature_layer_defaults_to_an_empty_feature_filter() -> None:
    layer = FeatureLayer(FeatureSpec(tag_filters={"highway": ["path"]}), Style())

    assert isinstance(layer.filter, FeatureFilter)
    assert layer.filter.areas is None


def test_style_to_svg_attrs_defaults() -> None:
    style = Style()

    assert style.to_svg_attrs() == {
        "stroke": "none",
        "stroke-width": "1.0pt",
        "fill": "none",
        "opacity": "1.0",
    }


def test_style_to_svg_attrs_includes_optional_opacity_fields() -> None:
    style = Style(
        stroke="#111111",
        stroke_width=2.5,
        fill="#eeeeee",
        opacity=0.7,
        stroke_opacity=0.4,
        fill_opacity=0.5,
    )

    assert style.to_svg_attrs() == {
        "stroke": "#111111",
        "stroke-width": "2.5pt",
        "fill": "#eeeeee",
        "opacity": "0.7",
        "stroke-opacity": "0.4",
        "fill-opacity": "0.5",
    }
