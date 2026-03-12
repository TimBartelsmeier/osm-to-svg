"""Convenience utility for one-shot SVG map creation."""

from tqdm.auto import tqdm

from osm_to_svg.features import FeatureSpec
from osm_to_svg.mapper import SvgMapper
from osm_to_svg.models import PoiStyle, Style


def create_map(
    *,
    pbf_path: str,
    scale: int = 100000,
    dpi: int = 300,
    bounds: tuple[float, float, float, float] | None = None,
    background_color: str | None = None,
    feature_layers: list[tuple[FeatureSpec, Style]] | None = None,
    poi_layers: list[tuple[list[tuple[float, float]], PoiStyle]] | None = None,
    output_path: str,
    show_progress: bool = False,
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
        scale: Map scale denominator (default: 100000 for 1:100,000). The scale is accurate at the centre latitude of the map bounds.
        dpi: Dots per inch for the output SVG (default: 300).
        bounds: Optional bounding box as (south_lat, west_lon, north_lat, east_lon).
            Passing this explicitly is recommended for predictable clipping and
            output dimensions.
        background_color: Optional SVG background color.
        feature_layers: Feature render instructions as
            ``[(feature_spec, style), ...]``.
        poi_layers: POI marker instructions as
            ``[(coords, poi_style), ...]`` where coords are ``[(lat, lon), ...]``.
        output_path: Destination path for the final combined SVG.
        show_progress: If ``True``, display a tqdm progress bar showing which
            layer is currently being processed (e.g., "Layer x/y").
            Defaults to ``False``.
    """
    n_feature_layers = len(feature_layers or [])
    n_poi_layers = len(poi_layers or [])
    total_layers = n_feature_layers + n_poi_layers

    progress_bar: tqdm | None = None
    if show_progress:
        progress_bar = tqdm(total=total_layers, leave=True, desc="Rendering map")

    try:
        with SvgMapper(
            pbf_path=pbf_path,
            scale=scale,
            dpi=dpi,
            bounds=bounds,
            background_color=background_color,
        ) as mapper:
            for i, (feature_spec, style) in enumerate(feature_layers or []):
                if progress_bar is not None:
                    progress_bar.set_description(f"Layer {i + 1}/{total_layers}")
                mapper.render_features(feature_spec, style, _progress_bar=None)
                if progress_bar is not None:
                    progress_bar.update(1)

            for j, (coords, poi_style) in enumerate(poi_layers or []):
                if progress_bar is not None:
                    progress_bar.set_description(
                        f"Layer {n_feature_layers + j + 1}/{total_layers}"
                    )
                mapper.place_poi_markers(
                    coords=coords, poi_style=poi_style, _progress_bar=None
                )
                if progress_bar is not None:
                    progress_bar.update(1)

            mapper.save(output_path)
    finally:
        if progress_bar is not None:
            progress_bar.close()
