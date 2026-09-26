"""Main SvgMapper class for the library."""

import xml.etree.ElementTree as ET
from collections.abc import Sequence
from pathlib import Path
from typing import Self

from osm_to_svg.features import FeatureSpec
from osm_to_svg.models import (
    AreaMatchMode,
    BoundingBox,
    FeatureLayer,
    PoiStyle,
    Polygon,
    Style,
)
from osm_to_svg.parsing import FeatureQuery, PBFParser
from osm_to_svg.projection import CoordinateTransformer
from osm_to_svg.rendering.combiner import combine_elements
from osm_to_svg.rendering.renderer import SVGRenderer

__all__ = ["SvgMapper"]


class SvgMapper:
    """Main class for creating SVG files from OpenStreetMap PBF data.

    This class provides a context manager interface for working with OSM data.
    The output SVG is generated with a specified scale (e.g., 1:100,000) and DPI,
    where the scale is accurate at the center latitude of the map.

    ``bounds`` is required for accurate clipping and predictable output
    dimensions. Some features (for example long roads) can extend beyond the
    intended region, so bounds define both the SVG size and clipping area.

    Example:
        >>> from osm_to_svg import features
        >>> with SvgMapper(
        ...     "city.osm.pbf",
        ...     scale=50000,
        ...     dpi=300,
        ...     bounds=((48.1, 11.5), (48.1, 11.6), (48.2, 11.6), (48.2, 11.5)),
        ...     background_color="#FFFFFF",
        ... ) as mapper:
        ...     mapper.render_features(
        ...         features.ROADS.MAJOR,
        ...         Style(stroke="#FF0000", stroke_width=2.0),
        ...     )
        ...     mapper.place_poi_markers(
        ...         [(48.1374, 11.5755)],
        ...         PoiStyle(marker_svg_path="marker.svg", scale=1.0),
        ...     )
        ...     mapper.save("final.svg")
    """

    def __init__(
        self,
        pbf_path: str,
        scale: int = 100000,
        dpi: int = 300,
        bounds: Polygon | None = None,
        background_color: str | None = None,
    ):
        """Initialize SvgMapper with a PBF file.

        Args:
            pbf_path: Path to the OpenStreetMap PBF file
            scale: Map scale denominator (default: 100000 for 1:100,000).
                  At this scale, 1km in reality corresponds to 1cm in the output.
                  The scale is accurate at the center latitude of the map bounds.
            dpi: Dots per inch for the output SVG (default: 300).
                 Standard values: 96 (web/screen), 72 (print), 300 (high-res print).
                 bounds: Required polygon as ``(latitude, longitude)`` vertices.
                     Explicit bounds avoid scanning the PBF solely to infer output
                     dimensions and clipping bounds.
            background_color: Optional background color for the SVG (e.g., "#FFFFFF", "white").
                            If None, the background will be transparent (default: None).
        """
        self.pbf_path = Path(pbf_path)
        self.scale = scale
        self.dpi = dpi
        self.background_color = background_color

        if not self.pbf_path.exists():
            raise FileNotFoundError(f"PBF file not found: {pbf_path}")
        if bounds is None:
            raise TypeError("bounds is required")
        self.custom_bounds = bounds
        self.parser: PBFParser | None = None
        self.transformer: CoordinateTransformer | None = None
        self.renderer: SVGRenderer | None = None
        self._layers: list[ET.Element] = []  # In-memory layer storage

    def __enter__(self) -> Self:
        """Enter context manager and initialize components."""
        # Initialize parser
        self.parser = PBFParser(str(self.pbf_path))

        # Initialize coordinate transformer
        self.transformer = CoordinateTransformer(
            self.custom_bounds, scale=self.scale, dpi=self.dpi
        )

        # Initialize renderer
        self.renderer = SVGRenderer(
            self.transformer, background_color=self.background_color
        )

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager."""
        # Cleanup if needed
        self.parser = None
        self.transformer = None
        self.renderer = None

    def render_features(
        self,
        features: FeatureSpec,
        style: Style,
        layer_id: str | None = None,
        _progress_bar=None,
        include_areas: Sequence[Polygon] | None = None,
        exclude_areas: Sequence[Polygon] | None = None,
        area_match_mode: AreaMatchMode = "intersects",
    ) -> None:
        """Render cartographic features and accumulate the layer in memory.

        Args:
            features: FeatureSpec describing which OSM features to render.
                     Use namespace classes from the ``features`` module, e.g.
                     ``features.ROADS.MAJOR`` or ``features.ROADS.MAJOR | features.WATER_POLYGONS.OPEN_WATER``.
            style: Style definition for the features
            layer_id: Optional ID for the SVG group.
                     Defaults to the joined tag filter keys (e.g. "highway").

        Example:
            >>> from osm_to_svg import features
            >>> mapper.render_features(
            ...     features.ROADS.MAJOR | features.WATER_POLYGONS.OPEN_WATER,
            ...     Style(stroke="#000000", fill="#4A90E2"),
            ... )
            >>> mapper.save("combined.svg")
        """
        if self.parser is None or self.renderer is None:
            raise RuntimeError("SvgMapper must be used as a context manager")

        # Extract features from PBF
        if _progress_bar is not None:
            _progress_bar.set_description("Parsing PBF...")
            _progress_bar.n = 0
            _progress_bar.total = None
            _progress_bar.refresh()
        if include_areas is None and exclude_areas is None:
            osm_features = self.parser.extract_features(features)
        else:
            osm_features = self.parser.extract_features(
                features,
                include_areas=include_areas,
                exclude_areas=exclude_areas,
                area_match_mode=area_match_mode,
            )
        if _progress_bar is not None:
            _progress_bar.set_description("Rendering features")
            _progress_bar.n = 0
            _progress_bar.total = len(osm_features)
            _progress_bar.refresh()

        # Determine layer ID
        if layer_id is None:
            layer_id = "_".join(sorted(features.tag_filters.keys()))
        layer_id = f"{len(self._layers)} {layer_id}"

        # Render to in-memory element and accumulate layer
        element = self.renderer.render_features(
            osm_features, style, layer_id, _progress_bar=_progress_bar
        )
        self._layers.append(element)

    def render_layer(self, layer: FeatureLayer, _progress_bar=None) -> None:
        """Render a configured feature layer."""
        self.render_features(
            layer.features,
            layer.style,
            layer_id=layer.layer_id,
            _progress_bar=_progress_bar,
            include_areas=layer.include_areas,
            exclude_areas=layer.exclude_areas,
            area_match_mode=layer.area_match_mode,
        )

    def render_layers(self, layers: Sequence[FeatureLayer], _progress_bar=None) -> None:
        """Render multiple feature layers using shared PBF traversals."""
        if self.parser is None or self.renderer is None:
            raise RuntimeError("SvgMapper must be used as a context manager")

        if not layers:
            return

        if _progress_bar is not None:
            _progress_bar.n = 0
            _progress_bar.total = None
            _progress_bar.set_description("Parsing PBF")
            _progress_bar.refresh()

        def on_parse_pass(completed: int, total: int) -> None:
            if _progress_bar is not None:
                _progress_bar.set_description(f"Parsing PBF ({completed}/{total})")
                _progress_bar.refresh()

        queries = [
            FeatureQuery(
                spec=layer.features,
                include_areas=layer.include_areas,
                exclude_areas=layer.exclude_areas,
                area_match_mode=layer.area_match_mode,
            )
            for layer in layers
        ]
        extracted_layers = self.parser.extract_features_for_queries(
            queries, _progress_callback=on_parse_pass
        )

        if _progress_bar is not None:
            _progress_bar.n = 0
            _progress_bar.total = sum(
                len(layer_features) for layer_features in extracted_layers
            )
            _progress_bar.set_description("Rendering features")
            _progress_bar.refresh()

        for layer, osm_features in zip(layers, extracted_layers, strict=True):
            layer_id = layer.layer_id
            if layer_id is None:
                layer_id = "_".join(sorted(layer.features.tag_filters.keys()))
            layer_id = f"{len(self._layers)} {layer_id}"
            element = self.renderer.render_features(
                osm_features,
                layer.style,
                layer_id,
                _progress_bar=_progress_bar,
            )
            self._layers.append(element)

    def place_poi_markers(
        self,
        coords: list[tuple[float, float]],
        poi_style: PoiStyle,
        layer_id: str | None = None,
        _progress_bar=None,
    ) -> None:
        """Place POI markers at specified geographic coordinates and accumulate the layer.

        The output layer will have the same dimensions as feature renders from
        the same PBF file, allowing proper layering.

        Args:
            coords: List of (latitude, longitude) tuples where markers should be placed
            poi_style: Marker style/configuration including marker SVG path, anchor,
                and exactly one sizing method (`scale`, `width_meters`, or `height_meters`).
            layer_id: Optional ID for the POI SVG group.
                Defaults to "pois".

        Example:
            >>> # Using scale parameter (relative sizing)
            >>> mapper.place_poi_markers(
            ...     [(48.1374, 11.5755), (48.1383, 11.5767)],
            ...     PoiStyle(marker_svg_path="pin.svg", scale=1.5),
            ... )
            >>>
            >>> # Using width_meters (absolute width in meters)
            >>> mapper.place_poi_markers(
            ...     [(48.1374, 11.5755)],
            ...     PoiStyle(marker_svg_path="pin.svg", width_meters=100.0)
            ... )
            >>> mapper.save("combined.svg")
        """
        if self.renderer is None:
            raise RuntimeError("SvgMapper must be used as a context manager")

        # Validate marker SVG exists
        if not Path(poi_style.marker_svg_path).exists():
            raise FileNotFoundError(
                f"Marker SVG file not found: {poi_style.marker_svg_path}"
            )

        # Determine layer ID
        if layer_id is None:
            layer_id = "pois"
        poi_layer_id = f"{len(self._layers)} {layer_id}"

        if _progress_bar is not None:
            _progress_bar.set_description("Placing markers")
            _progress_bar.n = 0
            _progress_bar.total = len(coords)
            _progress_bar.refresh()

        # Render POI markers in-memory and accumulate layer
        element = self.renderer.place_poi_markers(
            coords,
            poi_style,
            poi_layer_id,
            _progress_bar=_progress_bar,
        )
        self._layers.append(element)

    def save(self, output_path: str) -> None:
        """Save all accumulated in-memory layers to a combined SVG file.

        Combines all layers in the order they were rendered (first call = bottom layer).

        Args:
            output_path: Path where the combined SVG will be saved

        Raises:
            ValueError: If no layers have been accumulated

        Example:
            >>> with SvgMapper("city.osm.pbf") as mapper:
            ...     mapper.render_features(
            ...         features.WATER_POLYGONS.OPEN_WATER,
            ...         Style(fill="#4A90E2")
            ...     )
            ...     mapper.render_features(features.ROADS.MAJOR, Style(stroke="#000000"))
            ...     mapper.save("city_map.svg")
        """
        if not self._layers:
            raise ValueError(
                "No layers to combine. Call render_features() or place_poi_markers() "
                "without output_path to accumulate layers."
            )

        combine_elements(self._layers, output_path, self.background_color)

    def get_bounds(self) -> BoundingBox:
        """Get the geographic bounds of the PBF file.

        Returns:
            Tuple of (south_lat, west_lon, north_lat, east_lon)
        """
        if self.parser is None or self.transformer is None:
            raise RuntimeError("SvgMapper must be used as a context manager")

        return self.transformer.geo_bounds

    def get_dimensions(self) -> tuple[int, int]:
        """Get the SVG output dimensions.

        Returns:
            Tuple of (width, height) in pixels
        """
        if self.transformer is None:
            raise RuntimeError("SvgMapper must be used as a context manager")

        return self.transformer.get_dimensions()
