"""SVG rendering for OSM features and POI markers."""

import xml.etree.ElementTree as ET
from typing import Any

import svgwrite

from osm_to_svg.models import Feature, MarkerAnchor, PoiStyle, Style
from osm_to_svg.projection import CoordinateTransformer


class SVGRenderer:
    """Renders OSM features and POI markers as SVG files."""

    def __init__(
        self, transformer: CoordinateTransformer, background_color: str | None = None
    ):
        """Initialize renderer with coordinate transformer.

        Args:
            transformer: CoordinateTransformer for coordinate conversion
            background_color: Optional background color for SVG output (e.g., "#FFFFFF", "white").
                            If None, background will be transparent.
        """
        self.transformer = transformer
        self.background_color = background_color

    def render_features(
        self,
        features: list[Feature],
        style: Style,
        layer_id: str = "features",
    ) -> ET.Element:
        """Render features to an in-memory SVG element.

        Args:
            features: List of Feature objects to render
            style: Style definition for the features
            layer_id: ID for the SVG group element

        Returns:
            ET.Element representing the rendered layer
        """
        width, height = self.transformer.get_dimensions()
        viewbox = self.transformer.get_viewbox()

        # Create SVG drawing
        dwg = svgwrite.Drawing(
            ":memory:",
            size=(f"{width}px", f"{height}px"),
            viewBox=viewbox,
        )

        # Parse viewBox to get clipping boundaries
        vb_parts = viewbox.split()
        vb_x, vb_y, vb_width, vb_height = map(float, vb_parts)

        # Create clipping path to restrict rendering to bounding box
        clip_id = f"clip-{layer_id}"
        clip_path = dwg.defs.add(dwg.clipPath(id=clip_id))
        clip_path.add(
            dwg.rect(
                insert=(vb_x, vb_y),
                size=(vb_width, vb_height),
            )
        )

        # Create group for all features with clipping applied
        group = dwg.g(id=layer_id, clip_path=f"url(#{clip_id})")

        # Get style attributes
        style_attrs = style.to_svg_attrs()

        # Render each feature
        for feature in features:
            if len(feature.geometry) < 2:
                continue

            # Convert coordinates to SVG space.
            # Feature geometry stores coordinates as (lon, lat).
            svg_coords = [
                self.transformer.latlon_to_svg(lat, lon)
                for lon, lat in feature.geometry
            ]

            if feature.is_closed and len(svg_coords) >= 3:
                # Render as polygon (svgwrite expects list of tuples)
                group.add(dwg.polygon(points=svg_coords, **style_attrs))
            else:
                # Render as polyline (svgwrite expects list of tuples)
                group.add(dwg.polyline(points=svg_coords, **style_attrs))

        dwg.add(group)

        return self._drawing_to_element(dwg)

    def place_poi_markers(
        self,
        coords: list[tuple[float, float]],
        poi_style: PoiStyle,
        layer_id: str = "pois",
    ) -> ET.Element:
        """Place POI markers at specified coordinates and return an in-memory element.

        Args:
            coords: List of (lat, lon) coordinates where markers should be placed
            poi_style: POI marker styling and sizing configuration.
                Includes marker SVG path, anchor position, and exactly one sizing method
                (`scale`, `width_meters`, or `height_meters`).
            layer_id: ID for the SVG group containing the marker layer.

        Returns:
            ET.Element representing the rendered POI layer
        """
        scale = poi_style.scale
        width_meters = poi_style.width_meters
        height_meters = poi_style.height_meters
        anchor = poi_style.anchor

        width, height = self.transformer.get_dimensions()
        viewbox = self.transformer.get_viewbox()

        # Parse marker SVG to get its dimensions and content
        marker_tree = ET.parse(poi_style.marker_svg_path)
        marker_root = marker_tree.getroot()

        # Extract marker dimensions
        marker_width = self._parse_dimension(marker_root.get("width", "24"))
        marker_height = self._parse_dimension(marker_root.get("height", "24"))

        # Calculate scale from meters if specified
        if width_meters is not None:
            pixels_per_meter_x, _ = self.transformer.meters_to_pixels()
            scale = (width_meters * pixels_per_meter_x) / marker_width
        elif height_meters is not None:
            _, pixels_per_meter_y = self.transformer.meters_to_pixels()
            scale = (height_meters * pixels_per_meter_y) / marker_height

        # Create SVG drawing
        dwg = svgwrite.Drawing(
            ":memory:",
            size=(f"{width}px", f"{height}px"),
            viewBox=viewbox,
            debug=False,  # Disable validation for copying external SVG elements
        )

        # Parse viewBox to get clipping boundaries
        vb_parts = viewbox.split()
        vb_x, vb_y, vb_width, vb_height = map(float, vb_parts)

        # Create clipping path to restrict rendering to bounding box
        clip_id = f"clip-{layer_id}"
        clip_path = dwg.defs.add(dwg.clipPath(id=clip_id))
        clip_path.add(
            dwg.rect(
                insert=(vb_x, vb_y),
                size=(vb_width, vb_height),
            )
        )

        # Create main group for all POIs with clipping applied
        pois_group = dwg.g(id=layer_id, clip_path=f"url(#{clip_id})")

        # Place each POI marker
        for idx, (lat, lon) in enumerate(coords):
            svg_x, svg_y = self.transformer.latlon_to_svg(lat, lon)

            # Create group for this marker
            marker_group = dwg.g(id=f"poi-{idx}")

            # Calculate anchor point based on specified anchor position
            anchor_x, anchor_y = self._calculate_anchor_offset(
                svg_x, svg_y, marker_width, marker_height, scale, anchor
            )

            # Create nested SVG element for the marker
            marker_svg = dwg.add(
                dwg.svg(
                    x=anchor_x,
                    y=anchor_y,
                    width=marker_width * scale,
                    height=marker_height * scale,
                    viewBox=f"0 0 {marker_width} {marker_height}",
                )
            )

            # Add marker content (simplified approach: embed the marker's children)
            for child in marker_root:
                self._copy_element(child, marker_svg, dwg)

            marker_group.add(marker_svg)
            pois_group.add(marker_group)

        dwg.add(pois_group)

        return self._drawing_to_element(dwg)

    def _add_background(self, dwg: svgwrite.Drawing, viewbox: str) -> None:
        """Add a background rectangle to the SVG drawing.

        Args:
            dwg: svgwrite.Drawing object
            viewbox: ViewBox string in format "x y width height"
        """
        vb_parts = viewbox.split()
        vb_x, vb_y, vb_width, vb_height = map(float, vb_parts)

        # Insert background as the first element
        background = dwg.rect(
            insert=(vb_x, vb_y),
            size=(vb_width, vb_height),
            fill=self.background_color,
        )
        dwg.add(background)

    def _calculate_anchor_offset(
        self,
        svg_x: float,
        svg_y: float,
        marker_width: float,
        marker_height: float,
        scale: float,
        anchor: MarkerAnchor,
    ) -> tuple[float, float]:
        """Calculate marker position based on anchor point.

        Args:
            svg_x: X coordinate where marker should be anchored
            svg_y: Y coordinate where marker should be anchored
            marker_width: Width of the marker in pixels
            marker_height: Height of the marker in pixels
            scale: Scale factor applied to the marker
            anchor: Anchor position (e.g., "center", "bottom", "top-left")

        Returns:
            Tuple of (x, y) for the top-left corner of the marker
        """
        scaled_width = marker_width * scale
        scaled_height = marker_height * scale

        # Calculate offsets based on anchor position
        if anchor == "center":
            offset_x = -scaled_width / 2
            offset_y = -scaled_height / 2
        elif anchor == "top":
            offset_x = -scaled_width / 2
            offset_y = 0
        elif anchor == "top-right":
            offset_x = -scaled_width
            offset_y = 0
        elif anchor == "right":
            offset_x = -scaled_width
            offset_y = -scaled_height / 2
        elif anchor == "bottom-right":
            offset_x = -scaled_width
            offset_y = -scaled_height
        elif anchor == "bottom":
            offset_x = -scaled_width / 2
            offset_y = -scaled_height
        elif anchor == "bottom-left":
            offset_x = 0
            offset_y = -scaled_height
        elif anchor == "left":
            offset_x = 0
            offset_y = -scaled_height / 2
        elif anchor == "top-left":
            offset_x = 0
            offset_y = 0
        else:
            # Default to center if unknown anchor
            offset_x = -scaled_width / 2
            offset_y = -scaled_height / 2

        return (svg_x + offset_x, svg_y + offset_y)

    def _drawing_to_element(self, dwg: svgwrite.Drawing) -> ET.Element:
        """Convert svgwrite.Drawing to ElementTree.Element for in-memory use.

        Args:
            dwg: svgwrite.Drawing object

        Returns:
            ET.Element representing the SVG root
        """
        # Get SVG string from svgwrite
        svg_string = dwg.tostring()
        # Parse to ElementTree
        return ET.fromstring(svg_string)

    def _parse_dimension(self, value: str) -> float:
        """Parse dimension string (e.g., '24px', '24') to float."""
        if isinstance(value, (int, float)):
            return float(value)
        # Remove common units
        value = str(value).replace("px", "").replace("pt", "").strip()
        try:
            return float(value)
        except ValueError:
            return 24.0  # Default fallback

    def _copy_element(
        self,
        element: ET.Element,
        parent: Any,
        dwg: svgwrite.Drawing,
    ) -> None:
        """Recursively copy XML elements to svgwrite structure."""
        # This is a simplified approach - get tag name and attributes
        tag_name = element.tag.split("}")[-1]  # Remove namespace
        attrs = dict(element.attrib)

        # Map common SVG elements
        if tag_name == "circle":
            parent.add(
                dwg.circle(
                    center=(attrs.get("cx", 0), attrs.get("cy", 0)),
                    r=attrs.get("r", 0),
                    **{k: v for k, v in attrs.items() if k not in ["cx", "cy", "r"]},
                )
            )
        elif tag_name == "rect":
            parent.add(
                dwg.rect(
                    insert=(attrs.get("x", 0), attrs.get("y", 0)),
                    size=(attrs.get("width", 0), attrs.get("height", 0)),
                    **{
                        k: v
                        for k, v in attrs.items()
                        if k not in ["x", "y", "width", "height"]
                    },
                )
            )
        elif tag_name == "path":
            parent.add(
                dwg.path(
                    d=attrs.get("d", ""),
                    **{k: v for k, v in attrs.items() if k != "d"},
                )
            )
        elif tag_name == "g":
            group = dwg.g(**attrs)
            for child in element:
                self._copy_element(child, group, dwg)
            parent.add(group)
        # Add more element types as needed
