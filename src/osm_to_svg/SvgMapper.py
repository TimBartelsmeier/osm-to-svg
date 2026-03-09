"""Main SvgMapper class for the library."""

import xml.etree.ElementTree as ET
from pathlib import Path

from osm_to_svg.combiner import combine_elements
from osm_to_svg.features import FeatureSpec
from osm_to_svg.models import Style
from osm_to_svg.parser import PBFParser
from osm_to_svg.projection import CoordinateTransformer
from osm_to_svg.renderer import MarkerAnchor, SVGRenderer


class SvgMapper:
    """Main class for creating SVG files from OpenStreetMap PBF data.

    This class provides a context manager interface for working with OSM data.
    The output SVG is generated with a specified scale (e.g., 1:100,000) and DPI,
    where the scale is accurate at the center latitude of the map.

    Example:
        >>> from osm_to_svg import features
        >>> with SvgMapper("city.osm.pbf", scale=50000, dpi=96, background_color="#FFFFFF") as mapper:
        ...     mapper.render_features(
        ...         features.ROADS.MAJOR,
        ...         Style(stroke="#FF0000", stroke_width=2.0),
        ...     )
        ...     mapper.place_poi_markers(
        ...         "marker.svg", [(48.1374, 11.5755)], 1.0
        ...     )
        ...     mapper.save("final.svg")
    """

    def __init__(
        self,
        pbf_path: str,
        scale: int = 100000,
        dpi: int = 96,
        bounds: tuple[float, float, float, float] | None = None,
        background_color: str | None = None,
    ):
        """Initialize SvgMapper with a PBF file.

        Args:
            pbf_path: Path to the OpenStreetMap PBF file
            scale: Map scale denominator (default: 100000 for 1:100,000).
                  At this scale, 1km in reality corresponds to 1cm in the output.
                  The scale is accurate at the center latitude of the map bounds.
            dpi: Dots per inch for the output SVG (default: 96).
                 Standard values: 96 (web/screen), 72 (print), 300 (high-res print).
            bounds: Optional custom bounding box as (min_lon, min_lat, max_lon, max_lat).
                   If not provided, bounds will be extracted from the PBF file by scanning
                   all nodes, which may include nodes outside the area of interest.
            background_color: Optional background color for the SVG (e.g., "#FFFFFF", "white").
                            If None, the background will be transparent (default: None).
        """
        self.pbf_path = Path(pbf_path)
        self.scale = scale
        self.dpi = dpi
        self.custom_bounds = bounds
        self.background_color = background_color

        if not self.pbf_path.exists():
            raise FileNotFoundError(f"PBF file not found: {pbf_path}")

        self.parser: PBFParser | None = None
        self.transformer: CoordinateTransformer | None = None
        self.renderer: SVGRenderer | None = None
        self._layers: list[ET.Element] = []  # In-memory layer storage

    def __enter__(self) -> "SvgMapper":
        """Enter context manager and initialize components."""
        # Initialize parser
        self.parser = PBFParser(str(self.pbf_path))

        # Use custom bounds if provided, otherwise extract from PBF file
        if self.custom_bounds is not None:
            bounds = self.custom_bounds
        else:
            bounds = self.parser.get_bounds()

        # Initialize coordinate transformer
        self.transformer = CoordinateTransformer(bounds, scale=self.scale, dpi=self.dpi)

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
    ) -> None:
        """Render cartographic features and accumulate the layer in memory.

        Args:
            features: FeatureSpec describing which OSM features to render.
                     Use namespace classes from the ``features`` module, e.g.
                     ``features.ROADS.MAJOR`` or ``features.ROADS.MAJOR | features.WATER.BODIES``.
            style: Style definition for the features
            layer_id: Optional ID for the SVG group.
                     Defaults to the joined tag filter keys (e.g. "highway").

        Example:
            >>> from osm_to_svg import features
            >>> mapper.render_features(
            ...     features.ROADS.MAJOR | features.WATER.BODIES,
            ...     Style(stroke="#000000", fill="#4A90E2")
            ... )
            >>> mapper.save("combined.svg")
        """
        if self.parser is None or self.renderer is None:
            raise RuntimeError("SvgMapper must be used as a context manager")

        # Extract features from PBF
        osm_features = self.parser.extract_features(features)

        # Determine layer ID
        if layer_id is None:
            layer_id = "_".join(sorted(features.tag_filters.keys()))

        # Render to in-memory element and accumulate layer
        element = self.renderer.render_features(osm_features, style, layer_id)
        self._layers.append(element)

    def place_poi_markers(
        self,
        marker_svg_path: str,
        coords: list[tuple[float, float]],
        scale: float | None = None,
        anchor: MarkerAnchor = "center",
        width_meters: float | None = None,
        height_meters: float | None = None,
    ) -> None:
        """Place POI markers at specified geographic coordinates and accumulate the layer.

        The output layer will have the same dimensions as feature renders from
        the same PBF file, allowing proper layering.

        Marker size can be specified using scale (relative to original size),
        width_meters (absolute width in meters), or height_meters (absolute height in meters).
        Exactly one sizing method must be specified.

        Args:
            marker_svg_path: Path to SVG file to use as the marker icon
            coords: List of (latitude, longitude) tuples where markers should be placed
            scale: Scale factor for the markers (1.0 = original size, 2.0 = double size).
                   Mutually exclusive with width_meters/height_meters.
            anchor: Point of the marker that is anchored to the coordinate.
                   Options: "top", "top-right", "right", "bottom-right", "bottom",
                   "bottom-left", "left", "top-left", "center" (default: "center")
            width_meters: Desired marker width in meters. If specified, scale is calculated
                         to achieve this width. Mutually exclusive with scale and height_meters.
            height_meters: Desired marker height in meters. If specified, scale is calculated
                          to achieve this height. Mutually exclusive with scale and width_meters.

        Example:
            >>> # Using scale parameter (relative sizing)
            >>> mapper.place_poi_markers(
            ...     "pin.svg",
            ...     [(48.1374, 11.5755), (48.1383, 11.5767)],
            ...     scale=1.5,
            ... )
            >>>
            >>> # Using width_meters (absolute width in meters)
            >>> mapper.place_poi_markers(
            ...     "pin.svg",
            ...     [(48.1374, 11.5755)],
            ...     width_meters=100.0
            ... )
            >>> mapper.save("combined.svg")
        """
        if self.renderer is None:
            raise RuntimeError("SvgMapper must be used as a context manager")

        # Validate marker SVG exists
        if not Path(marker_svg_path).exists():
            raise FileNotFoundError(f"Marker SVG file not found: {marker_svg_path}")

        # Render POI markers in-memory and accumulate layer
        element = self.renderer.place_poi_markers(
            marker_svg_path,
            coords,
            scale,
            anchor,
            width_meters,
            height_meters,
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
            ...     mapper.render_features(features.WATER.BODIES, Style(fill="#4A90E2"))
            ...     mapper.render_features(features.ROADS.MAJOR, Style(stroke="#000000"))
            ...     mapper.save("city_map.svg")
        """
        if not self._layers:
            raise ValueError(
                "No layers to combine. Call render_features() or place_poi_markers() "
                "without output_path to accumulate layers."
            )

        combine_elements(self._layers, output_path, self.background_color)

    def get_bounds(self) -> tuple[float, float, float, float]:
        """Get the geographic bounds of the PBF file.

        Returns:
            Tuple of (min_lon, min_lat, max_lon, max_lat)
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
