from osm_to_svg.features import FeatureSpec
from osm_to_svg.models import FeatureLayer, OsmObjectId, Style


def test_osm_object_id_is_typed_and_stringifiable() -> None:
    object_id = OsmObjectId("relation", 123)

    assert str(object_id) == "relation/123"


def test_osm_object_id_rejects_non_positive_values() -> None:
    import pytest

    with pytest.raises(ValueError, match="greater than 0"):
        OsmObjectId("way", 0)


def test_feature_layer_accepts_areas() -> None:
    bbox = ((52.0, 9.0), (52.0, 9.1), (52.1, 9.1), (52.1, 9.0))
    layer = FeatureLayer(
        FeatureSpec(tag_filters={"leisure": ["park"]}),
        Style(fill="green"),
        areas=[bbox],
    )

    assert layer.areas == ((*bbox, bbox[0]),)


def test_feature_layer_rejects_empty_limits() -> None:
    import pytest

    spec = FeatureSpec(tag_filters={"leisure": ["park"]})
    with pytest.raises(ValueError, match="areas must not be empty"):
        FeatureLayer(spec, Style(), areas=[])
    with pytest.raises(ValueError, match="object_ids must not be empty"):
        FeatureLayer(spec, Style(), object_ids=[])


def test_feature_layer_accepts_multiple_areas() -> None:
    first = ((52.0, 9.0), (52.0, 9.1), (52.1, 9.1), (52.1, 9.0))
    second = ((53.0, 10.0), (53.0, 10.1), (53.1, 10.1), (53.1, 10.0))
    layer = FeatureLayer(
        FeatureSpec(tag_filters={"leisure": ["park"]}),
        Style(fill="green"),
        areas=[first, second],
    )

    assert layer.areas == ((*first, first[0]), (*second, second[0]))


def test_feature_layer_accepts_areas_and_object_ids() -> None:
    bbox = ((52.0, 9.0), (52.0, 9.1), (52.1, 9.1), (52.1, 9.0))
    layer = FeatureLayer(
        FeatureSpec(tag_filters={"leisure": ["park"]}),
        Style(fill="green"),
        areas=[bbox],
        object_ids={OsmObjectId("way", 123)},
    )

    assert layer.areas == ((*bbox, bbox[0]),)
    assert layer.object_ids == frozenset({OsmObjectId("way", 123)})


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
