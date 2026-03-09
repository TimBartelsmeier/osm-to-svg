"""Convenience utility for one-shot SVG map creation."""

from osm_to_svg.features import FeatureSpec
from osm_to_svg.models import PoiStyle, Style
from osm_to_svg.SvgMapper import SvgMapper


def create_map(
    *,
    pbf_path: str,
    scale: int = 100000,
    dpi: int = 96,
    bounds: tuple[float, float, float, float] | None = None,
    background_color: str | None = None,
    feature_layers: list[tuple[FeatureSpec, Style]] | None = None,
    poi_layers: list[tuple[list[tuple[float, float]], PoiStyle]] | None = None,
    output_path: str,
) -> None:
    """Create an SVG map using a single convenience call.

    This utility wraps the standard ``SvgMapper`` workflow: initialize the
    mapper, render feature layers, place POI marker layers, and save the
    combined output.

    It is recommended to pass ``bounds`` explicitly even if the source PBF is
    already cropped to the region of interest. Some features (for example long
    roads) can extend beyond the selected region, and explicit bounds ensure
    the SVG is sized and clipped to the intended area.

    Args:
        pbf_path: Path to the OpenStreetMap PBF file.
        scale: Map scale denominator (default: 100000 for 1:100,000).
        dpi: Dots per inch for the output SVG (default: 96).
        bounds: Optional bounding box as (min_lon, min_lat, max_lon, max_lat).
            Passing this explicitly is recommended for predictable clipping and
            output dimensions.
        background_color: Optional SVG background color.
        feature_layers: Feature render instructions as
            ``[(feature_spec, style), ...]``.
        poi_layers: POI marker instructions as
            ``[(coords, poi_style), ...]`` where coords are ``[(lat, lon), ...]``.
        output_path: Destination path for the final combined SVG.
    """
    with SvgMapper(
        pbf_path=pbf_path,
        scale=scale,
        dpi=dpi,
        bounds=bounds,
        background_color=background_color,
    ) as mapper:
        for feature_spec, style in feature_layers or []:
            mapper.render_features(feature_spec, style)

        for coords, poi_style in poi_layers or []:
            mapper.place_poi_markers(coords=coords, poi_style=poi_style)

        mapper.save(output_path)
