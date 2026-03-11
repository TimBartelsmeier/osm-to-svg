"""SVG rendering for OSM features and POI markers."""

import re
import xml.etree.ElementTree as ET
from typing import Any

import svgwrite

from osm_to_svg.models import Feature, MarkerAnchor, PoiStyle, Style
from osm_to_svg.projection import CoordinateTransformer
from osm_to_svg.rendering.svg_utils import copy_svg_element, parse_svg_dimension

__all__ = ["SVGRenderer"]


class SVGRenderer:
    """Renders OSM features and POI markers as SVG files."""

    def __init__(
        self, transformer: CoordinateTransformer, background_color: str | None = None
    ):
        """Initialize the renderer with a coordinate transformer.

        Args:
            transformer: Coordinate transformer used to project lat/lon to SVG space.
            background_color: Optional background fill color for generated SVG layers.
        """
        self.transformer = transformer
        self._background_color = background_color

    def render_features(
        self,
        features: list[Feature],
        style: Style,
        layer_id: str = "features",
    ) -> ET.Element:
        """Render a list of OSM features to an SVG ``<svg>`` element.

        Each feature is drawn as a ``<polygon>`` (closed geometry) or
        ``<polyline>`` (open geometry) with the given style applied.

        Args:
            features: OSM features to render.
            style: SVG style (stroke, fill, opacity, …) applied to every element.
            layer_id: ``id`` attribute for the wrapping ``<g>`` group (default: ``"features"``).

        Returns:
            Root ``<svg>`` element containing a clipped group of rendered shapes.
        """
        width, height = self.transformer.get_dimensions()
        viewbox = self.transformer.get_viewbox()

        dwg = svgwrite.Drawing(
            ":memory:",
            size=(f"{width}px", f"{height}px"),
            viewBox=viewbox,
        )

        vb_parts = viewbox.split()
        vb_x, vb_y, vb_width, vb_height = map(float, vb_parts)

        safe_layer_id = self._sanitize_svg_id(layer_id, prefix="layer")
        clip_id = f"clip-{safe_layer_id}"
        clip_path = dwg.defs.add(dwg.clipPath(id=clip_id))
        clip_path.add(
            dwg.rect(
                insert=(vb_x, vb_y),
                size=(vb_width, vb_height),
            )
        )

        group = dwg.g(id=safe_layer_id, clip_path=f"url(#{clip_id})")
        style_attrs = style.to_svg_attrs()

        for feature in features:
            if len(feature.geometry) < 2:
                continue

            svg_coords = [
                self.transformer.latlon_to_svg(lat, lon)
                for lat, lon in feature.geometry
            ]

            if feature.is_closed and len(svg_coords) >= 3:
                group.add(dwg.polygon(points=svg_coords, **style_attrs))
            else:
                group.add(dwg.polyline(points=svg_coords, **style_attrs))

        dwg.add(group)
        return self._drawing_to_element(dwg)

    def place_poi_markers(
        self,
        coords: list[tuple[float, float]],
        poi_style: PoiStyle,
        layer_id: str = "pois",
    ) -> ET.Element:
        """Render POI markers at geographic coordinates and return an SVG ``<svg>`` element.

        The marker SVG is read from ``poi_style.marker_svg_path`` and placed at
        each coordinate using the anchor point and sizing method defined in
        ``poi_style``.

        Args:
            coords: List of ``(latitude, longitude)`` tuples.
            poi_style: Marker configuration including path, anchor, and sizing.
            layer_id: ``id`` attribute for the wrapping ``<g>`` group (default: ``"pois"``).

        Returns:
            Root ``<svg>`` element containing a clipped group of placed markers.
        """
        scale = poi_style.scale
        width_meters = poi_style.width_meters
        height_meters = poi_style.height_meters
        anchor = poi_style.anchor

        width, height = self.transformer.get_dimensions()
        viewbox = self.transformer.get_viewbox()

        marker_tree = ET.parse(poi_style.marker_svg_path)
        marker_root = marker_tree.getroot()

        marker_width = self._parse_svg_dimension(marker_root.get("width", "24"))
        marker_height = self._parse_svg_dimension(marker_root.get("height", "24"))

        if width_meters is not None:
            pixels_per_meter_x, _ = self.transformer.meters_to_pixels()
            scale = (width_meters * pixels_per_meter_x) / marker_width
        elif height_meters is not None:
            _, pixels_per_meter_y = self.transformer.meters_to_pixels()
            scale = (height_meters * pixels_per_meter_y) / marker_height

        dwg = svgwrite.Drawing(
            ":memory:",
            size=(f"{width}px", f"{height}px"),
            viewBox=viewbox,
            debug=False,
        )

        vb_parts = viewbox.split()
        vb_x, vb_y, vb_width, vb_height = map(float, vb_parts)

        safe_layer_id = self._sanitize_svg_id(layer_id, prefix="layer")
        clip_id = f"clip-{safe_layer_id}"
        clip_path = dwg.defs.add(dwg.clipPath(id=clip_id))
        clip_path.add(
            dwg.rect(
                insert=(vb_x, vb_y),
                size=(vb_width, vb_height),
            )
        )

        pois_group = dwg.g(id=safe_layer_id, clip_path=f"url(#{clip_id})")

        for idx, (lat, lon) in enumerate(coords):
            svg_x, svg_y = self.transformer.latlon_to_svg(lat, lon)
            marker_group = dwg.g(id=f"poi-{idx}")
            anchor_x, anchor_y = self._calculate_anchor_offset(
                svg_x, svg_y, marker_width, marker_height, scale, anchor
            )

            marker_svg = dwg.add(
                dwg.svg(
                    x=anchor_x,
                    y=anchor_y,
                    width=marker_width * scale,
                    height=marker_height * scale,
                    viewBox=f"0 0 {marker_width} {marker_height}",
                )
            )

            for child in marker_root:
                self._copy_svg_subtree(child, marker_svg, dwg)

            marker_group.add(marker_svg)
            pois_group.add(marker_group)

        dwg.add(pois_group)
        return self._drawing_to_element(dwg)

    def _calculate_anchor_offset(
        self,
        svg_x: float,
        svg_y: float,
        marker_width: float,
        marker_height: float,
        scale: float,
        anchor: MarkerAnchor,
    ) -> tuple[float, float]:
        """Return the top-left SVG insertion point for a marker given its anchor."""
        scaled_width = marker_width * scale
        scaled_height = marker_height * scale

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
            offset_x = -scaled_width / 2
            offset_y = -scaled_height / 2

        return (svg_x + offset_x, svg_y + offset_y)

    def _drawing_to_element(self, dwg: svgwrite.Drawing) -> ET.Element:
        """Serialize an svgwrite Drawing to an ElementTree Element."""
        svg_string = dwg.tostring()
        return ET.fromstring(svg_string)

    def _parse_svg_dimension(self, value: str | int | float) -> float:
        """Delegate to :func:`~osm_to_svg.rendering.svg_utils.parse_svg_dimension`."""
        return parse_svg_dimension(value)

    def _sanitize_svg_id(self, value: str, prefix: str = "id") -> str:
        """Return a valid SVG id by replacing non-alphanumeric characters with hyphens."""
        normalized = re.sub(r"[^A-Za-z0-9_.\-]+", "-", value.strip()).strip("-")
        if not normalized:
            return prefix
        if normalized[0].isdigit() or normalized[0] in {"-", "."}:
            return f"{prefix}-{normalized}"
        return normalized

    def _parse_dimension(self, value: str | int | float) -> float:
        """Alias for :meth:`_parse_svg_dimension`."""
        return self._parse_svg_dimension(value)

    def _copy_svg_subtree(
        self,
        element: ET.Element,
        parent: Any,
        dwg: svgwrite.Drawing,
    ) -> None:
        """Delegate to :func:`~osm_to_svg.rendering.svg_utils.copy_svg_element`."""
        copy_svg_element(element, parent, dwg)

    def _copy_element(
        self,
        element: ET.Element,
        parent: Any,
        dwg: svgwrite.Drawing,
    ) -> None:
        """Alias for :meth:`_copy_svg_subtree`."""
        self._copy_svg_subtree(element, parent, dwg)
