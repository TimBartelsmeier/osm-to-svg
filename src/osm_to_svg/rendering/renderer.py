"""SVG rendering for OSM features and POI markers."""

import re
import xml.etree.ElementTree as ET
from typing import Any

import svgwrite

from osm_to_svg.models import Feature, MarkerAnchor, PoiStyle, Style
from osm_to_svg.projection import CoordinateTransformer
from osm_to_svg.rendering.svg_utils import copy_svg_element, parse_svg_dimension

__all__ = ["SVGRenderer"]

SVG_NS = "http://www.w3.org/2000/svg"


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
        _progress_bar=None,
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

        ET.register_namespace("", SVG_NS)
        root = ET.Element(
            f"{{{SVG_NS}}}svg",
            {
                "width": f"{width}px",
                "height": f"{height}px",
                "viewBox": viewbox,
            },
        )
        safe_layer_id = self._sanitize_svg_id(layer_id, prefix="layer")
        clip_id = f"clip-{safe_layer_id}"
        defs = ET.SubElement(root, f"{{{SVG_NS}}}defs")
        clip_path = ET.SubElement(defs, f"{{{SVG_NS}}}clipPath", {"id": clip_id})
        ET.SubElement(
            clip_path,
            f"{{{SVG_NS}}}polygon",
            {"points": self._points_attribute(self.transformer.svg_polygon)},
        )
        group = ET.SubElement(
            root,
            f"{{{SVG_NS}}}g",
            {"id": safe_layer_id, "clip-path": f"url(#{clip_id})"},
        )
        style_attrs = style.to_svg_attrs()

        for feature in features:
            if len(feature.geometry) < 2:
                if _progress_bar is not None:
                    _progress_bar.update(1)
                continue

            project_geometry = getattr(self.transformer, "geometry_to_svg", None)
            if project_geometry is None:
                svg_coords = tuple(
                    self.transformer.latlon_to_svg(lat, lon)
                    for lat, lon in feature.geometry
                )
            else:
                svg_coords = project_geometry(feature.geometry)

            if feature.inner_geometries:
                projected_rings = [svg_coords]
                if project_geometry is None:
                    projected_rings.extend(
                        tuple(
                            self.transformer.latlon_to_svg(lat, lon)
                            for lat, lon in inner_geometry
                        )
                        for inner_geometry in feature.inner_geometries
                    )
                else:
                    projected_rings.extend(
                        project_geometry(inner_geometry)
                        for inner_geometry in feature.inner_geometries
                    )
                tag = "path"
            elif feature.is_closed and len(svg_coords) >= 3:
                tag = "polygon"
            else:
                tag = "polyline"
            if feature.inner_geometries:
                feature_attrs = {
                    "d": self._path_attribute(projected_rings),
                    "fill-rule": "evenodd",
                    **style_attrs,
                }
            else:
                feature_attrs = {
                    "points": self._points_attribute(svg_coords),
                    **style_attrs,
                }
            if feature.object_id is not None:
                feature_attrs["id"] = self._sanitize_svg_id(
                    str(feature.object_id), prefix="feature"
                )
            ET.SubElement(
                group,
                f"{{{SVG_NS}}}{tag}",
                feature_attrs,
            )

            if _progress_bar is not None:
                _progress_bar.update(1)

        return root

    @staticmethod
    def _points_attribute(points: Any) -> str:
        """Format coordinate pairs using SVG's points attribute syntax."""
        return " ".join(f"{x},{y}" for x, y in points)

    @staticmethod
    def _path_attribute(rings: Any) -> str:
        """Format closed coordinate rings as an SVG path with subpaths."""
        return " ".join(
            "M " + " L ".join(f"{x},{y}" for x, y in ring) + " Z" for ring in rings
        )

    def place_poi_markers(
        self,
        coords: list[tuple[float, float]],
        poi_style: PoiStyle,
        layer_id: str = "pois",
        _progress_bar=None,
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
        scale = poi_style.scale if poi_style.scale is not None else 1.0
        width_meters = poi_style.width_meters
        height_meters = poi_style.height_meters
        anchor = poi_style.anchor

        width, height = self.transformer.get_dimensions()
        map_viewbox = self.transformer.get_viewbox()

        marker_tree = ET.parse(poi_style.marker_svg_path)
        marker_root = marker_tree.getroot()

        marker_viewbox = self._parse_viewbox(marker_root.get("viewBox"))
        marker_width = self._parse_svg_dimension(
            marker_root.get("width", "24"),
            fallback=marker_viewbox[2] if marker_viewbox else 24.0,
        )
        marker_height = self._parse_svg_dimension(
            marker_root.get("height", "24"),
            fallback=marker_viewbox[3] if marker_viewbox else 24.0,
        )

        if width_meters is not None:
            pixels_per_meter_x, _ = self.transformer.meters_to_pixels()
            scale = (width_meters * pixels_per_meter_x) / marker_width
        elif height_meters is not None:
            _, pixels_per_meter_y = self.transformer.meters_to_pixels()
            scale = (height_meters * pixels_per_meter_y) / marker_height

        dwg = svgwrite.Drawing(
            ":memory:",
            size=(f"{width}px", f"{height}px"),
            viewBox=map_viewbox,
            debug=False,
        )

        safe_layer_id = self._sanitize_svg_id(layer_id, prefix="layer")
        clip_id = f"clip-{safe_layer_id}"
        clip_path = dwg.defs.add(dwg.clipPath(id=clip_id))
        clip_path.add(dwg.polygon(points=self.transformer.svg_polygon))

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

            if _progress_bar is not None:
                _progress_bar.update(1)

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

    def _parse_svg_dimension(self, value: str | float, fallback: float = 24.0) -> float:
        """Delegate to :func:`~osm_to_svg.rendering.svg_utils.parse_svg_dimension`."""
        return parse_svg_dimension(value, fallback=fallback)

    def _parse_viewbox(
        self, value: str | None
    ) -> tuple[float, float, float, float] | None:
        """Parse an SVG viewBox, returning ``None`` for missing or invalid values."""
        if value is None:
            return None
        try:
            parts = [float(part) for part in re.split(r"[ ,]+", value.strip())]
        except ValueError:
            return None
        if len(parts) != 4 or parts[2] <= 0 or parts[3] <= 0:
            return None
        return tuple(parts)  # type: ignore[return-value]

    def _sanitize_svg_id(self, value: str, prefix: str = "id") -> str:
        """Return a valid SVG id by replacing non-alphanumeric characters with hyphens."""
        normalized = re.sub(r"[^A-Za-z0-9_.\-]+", "-", value.strip()).strip("-")
        if not normalized:
            return prefix
        if normalized[0].isdigit() or normalized[0] in {"-", "."}:
            return f"{prefix}-{normalized}"
        return normalized

    def _parse_dimension(self, value: str | float) -> float:
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
