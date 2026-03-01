"""Main SvgMapper class for the library."""

import xml.etree.ElementTree as ET
from enum import Enum
from pathlib import Path

from osm_to_svg.combiner import combine_elements, combine_svgs
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
        >>> with SvgMapper("city.osm.pbf", scale=50000, dpi=96, background_color="#FFFFFF") as mapper:
        ...     mapper.render_features(
        ...         RoadType, [RoadType.MOTORWAY],
        ...         Style(stroke="#FF0000", stroke_width=2.0),
        ...         "roads.svg"
        ...     )
        ...     mapper.place_poi_markers(
        ...         "marker.svg", [(48.1374, 11.5755)], 1.0, "pois.svg"
        ...     )
        ...     mapper.combine(["roads.svg", "pois.svg"], "final.svg")
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
        feature_type: type[Enum],
        subtypes: list[Enum] | None,
        style: Style,
        output_path: str | None = None,
        layer_id: str | None = None,
    ) -> None:
        """Render specific cartographic features to an SVG file or accumulate in-memory.

        Args:
            feature_type: Type of features to render (RoadType, RailwayType, etc.)
            subtypes: Optional list of specific subtypes to render.
                     If None, all subtypes are rendered.
            style: Style definition for the features
            output_path: Path where the SVG file will be saved.
                        If None, layer is accumulated in memory for later combining.
            layer_id: Optional ID for the SVG group (default: feature type name)

        Example:
            >>> # Save directly to file (backward compatible)
            >>> mapper.render_features(
            ...     RoadType,
            ...     [RoadType.MOTORWAY, RoadType.PRIMARY],
            ...     Style(stroke="#FF0000", stroke_width=2.0),
            ...     "roads.svg"
            ... )
            >>>
            >>> # Accumulate in memory for combining
            >>> mapper.render_features(
            ...     RoadType,
            ...     [RoadType.MOTORWAY],
            ...     Style(stroke="#FF0000", stroke_width=2.0)
            ... )
            >>> mapper.save_combined("combined.svg")
        """
        if self.parser is None or self.renderer is None:
            raise RuntimeError("SvgMapper must be used as a context manager")

        # Extract features from PBF
        features = self.parser.extract_features(feature_type, subtypes)

        # Determine layer ID
        if layer_id is None:
            layer_id = feature_type.__name__.lower()

        # Render to SVG (file or in-memory)
        element = self.renderer.render_features(features, style, output_path, layer_id)

        # If in-memory mode, accumulate layer
        if output_path is None and element is not None:
            self._layers.append(element)

    def place_poi_markers(
        self,
        marker_svg_path: str,
        coords: list[tuple[float, float]],
        scale: float | None = None,
        output_path: str | None = None,
        anchor: MarkerAnchor = "center",
        width_meters: float | None = None,
        height_meters: float | None = None,
    ) -> None:
        """Place POI markers at specified geographic coordinates.

        The output SVG will have the same dimensions as feature renders from
        the same PBF file, allowing proper layering.

        Marker size can be specified using scale (relative to original size),
        width_meters (absolute width in meters), or height_meters (absolute height in meters).
        Exactly one sizing method must be specified.

        Args:
            marker_svg_path: Path to SVG file to use as the marker icon
            coords: List of (latitude, longitude) tuples where markers should be placed
            scale: Scale factor for the markers (1.0 = original size, 2.0 = double size).
                   Mutually exclusive with width_meters/height_meters.
            output_path: Path where the SVG file will be saved.
                        If None, layer is accumulated in memory for later combining.
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
            ...     output_path="pois.svg"
            ... )
            >>>
            >>> # Using width_meters (absolute width in meters)
            >>> mapper.place_poi_markers(
            ...     "pin.svg",
            ...     [(48.1374, 11.5755)],
            ...     width_meters=100.0
            ... )
            >>>
            >>> # Using height_meters (absolute height in meters)
            >>> mapper.place_poi_markers(
            ...     "pin.svg",
            ...     [(48.1374, 11.5755)],
            ...     height_meters=50.0
            ... )
            >>> mapper.save_combined("combined.svg")
        """
        if self.renderer is None:
            raise RuntimeError("SvgMapper must be used as a context manager")

        # Validate marker SVG exists
        if not Path(marker_svg_path).exists():
            raise FileNotFoundError(f"Marker SVG file not found: {marker_svg_path}")

        # Render POI markers (file or in-memory)
        element = self.renderer.place_poi_markers(
            marker_svg_path,
            coords,
            scale,
            output_path,
            anchor,
            width_meters,
            height_meters,
        )

        # If in-memory mode, accumulate layer
        if output_path is None and element is not None:
            self._layers.append(element)

    def combine(self, svg_paths: list[str], output_path: str) -> None:
        """Combine multiple SVG files into a single layered file.

        The order of svg_paths determines the z-order (first is bottom,
        last is top). Each input SVG is wrapped in a group in the output.

        This method is for combining existing SVG files. For in-memory layer
        composition, use save_combined() instead.

        Args:
            svg_paths: List of paths to SVG files to combine
            output_path: Path where the combined SVG will be saved

        Example:
            >>> mapper.combine(
            ...     ["water.svg", "roads.svg", "buildings.svg", "pois.svg"],
            ...     "final_map.svg"
            ... )
        """
        combine_svgs(svg_paths, output_path)

    def save_combined(self, output_path: str) -> None:
        """Save all accumulated in-memory layers to a combined SVG file.

        This method combines all layers rendered with output_path=None
        into a single SVG file. The z-order is determined by the order
        in which render methods were called (first call = bottom layer).

        Args:
            output_path: Path where the combined SVG will be saved

        Raises:
            ValueError: If no layers have been accumulated

        Example:
            >>> with SvgMapper("city.osm.pbf") as mapper:
            ...     # Render multiple layers without saving to disk
            ...     mapper.render_features(WaterwayType, None, water_style)
            ...     mapper.render_features(RoadType, None, road_style)
            ...     mapper.render_features(BuildingType, None, building_style)
            ...     # Save all layers combined
            ...     mapper.save_combined("city_map.svg")
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
