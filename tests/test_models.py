from osm_to_svg.models import Style


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
