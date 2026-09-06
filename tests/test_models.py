import pytest

from osm_to_svg.features import FeatureSpec
from osm_to_svg.models import FeatureLayer, OsmObjectId, Style


def test_osm_object_id_is_typed_and_stringifiable() -> None:
    object_id = OsmObjectId("relation", 123)

    assert str(object_id) == "relation/123"


def test_feature_layer_accepts_bboxes() -> None:
    layer = FeatureLayer(
        FeatureSpec(tag_filters={"leisure": ["park"]}),
        Style(fill="green"),
        bboxes=[(52.0, 9.0, 52.1, 9.1)],
    )

    assert layer.bboxes == ((52.0, 9.0, 52.1, 9.1),)


def test_feature_layer_accepts_multiple_bboxes() -> None:
    layer = FeatureLayer(
        FeatureSpec(tag_filters={"leisure": ["park"]}),
        Style(fill="green"),
        bboxes=[(52.0, 9.0, 52.1, 9.1), (53.0, 10.0, 53.1, 10.1)],
    )

    assert layer.bboxes == ((52.0, 9.0, 52.1, 9.1), (53.0, 10.0, 53.1, 10.1))


def test_feature_layer_rejects_both_limits() -> None:
    with pytest.raises(ValueError, match="either bboxes or object_ids"):
        FeatureLayer(
            FeatureSpec(tag_filters={"leisure": ["park"]}),
            Style(fill="green"),
            bboxes=[(52.0, 9.0, 52.1, 9.1)],
            object_ids={OsmObjectId("way", 123)},
        )


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
