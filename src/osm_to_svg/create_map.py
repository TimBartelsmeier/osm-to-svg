"""Convenience utility for one-shot SVG map creation."""

from tqdm.auto import tqdm

from osm_to_svg.mapper import SvgMapper
from osm_to_svg.models import FeatureLayer, PoiStyle, Polygon


def create_map(
    *,
    pbf_path: str,
    scale: int = 100000,
    dpi: int = 300,
    bounds: Polygon,
    background_color: str | None = None,
    feature_layers: list[FeatureLayer] | None = None,
    poi_layers: list[tuple[list[tuple[float, float]], PoiStyle]] | None = None,
    output_path: str,
    show_progress: bool = False,
) -> None:
    """Create an SVG map using a single convenience call.

    This utility wraps the standard ``SvgMapper`` workflow: initialize the
    mapper, render feature layers, place POI marker layers, and save the
    combined output.

    ``bounds`` is required. This avoids scanning the entire PBF solely to infer
    output dimensions and clipping bounds. Some features (for example long
    roads) can extend beyond the selected region, so explicit bounds also ensure
    the SVG is sized and clipped to the intended area.

    Args:
        pbf_path: Path to the OpenStreetMap PBF file.
        scale: Map scale denominator (default: 100000 for 1:100,000). The scale is accurate at the centre latitude of the map bounds.
        dpi: Dots per inch for the output SVG (default: 300).
        bounds: Required polygon as ``(latitude, longitude)`` vertices.
        background_color: Optional SVG background color.
        feature_layers: Feature render instructions as a list of
            :class:`~osm_to_svg.models.FeatureLayer` objects.
        poi_layers: POI marker instructions as
            ``[(coords, poi_style), ...]`` where coords are ``[(lat, lon), ...]``.
        output_path: Destination path for the final combined SVG.
        show_progress: If ``True``, display a tqdm progress bar showing which
            parsing pass and rendering work are currently being processed.
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
            normalized_feature_layers = list(feature_layers or [])
            if any(
                not isinstance(layer, FeatureLayer)
                for layer in normalized_feature_layers
            ):
                raise TypeError("feature_layers must contain FeatureLayer objects")
            if progress_bar is not None:
                progress_bar.n = 0
                progress_bar.total = 0
                progress_bar.set_description("Preparing map")
                progress_bar.refresh()
            mapper.render_layers(normalized_feature_layers, _progress_bar=progress_bar)
            if progress_bar is not None:
                progress_bar.total = (progress_bar.total or 0) + sum(
                    len(coords) for coords, _ in (poi_layers or [])
                )
                progress_bar.refresh()

            for coords, poi_style in poi_layers or []:
                if progress_bar is not None:
                    progress_bar.set_description("Placing POI markers")
                mapper.place_poi_markers(
                    coords=coords, poi_style=poi_style, _progress_bar=progress_bar
                )

            mapper.save(output_path)
    finally:
        if progress_bar is not None:
            progress_bar.close()
