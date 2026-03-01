"""Data models for styling and feature representation."""

from dataclasses import dataclass

from pydantic import BaseModel, Field


class Style(BaseModel):
    """Style definition for SVG elements.

    Default style has no stroke and no fill. Specify stroke and/or fill colors to make elements visible.

    Attributes:
        stroke: Stroke color (CSS color string, e.g., '#000000', 'red', 'rgb(0,0,0)') or 'none' for no stroke (default: 'none')
        stroke_width: Stroke width in points (pt) (default: 1.0)
        fill: Fill color (CSS color string) or 'none' for no fill (default: 'none')
        opacity: Overall opacity (0.0 to 1.0) (default: 1.0)
        stroke_opacity: Stroke opacity (0.0 to 1.0) (default: None)
        fill_opacity: Fill opacity (0.0 to 1.0) (default: None)
    """

    stroke: str = Field(default="none", description="Stroke color")
    stroke_width: float = Field(default=1.0, ge=0, description="Stroke width in points")
    fill: str = Field(default="none", description="Fill color")
    opacity: float = Field(default=1.0, ge=0.0, le=1.0, description="Overall opacity")
    stroke_opacity: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Stroke opacity"
    )
    fill_opacity: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Fill opacity"
    )

    def to_svg_attrs(self) -> dict[str, str]:
        """Convert style to SVG attribute dictionary."""
        attrs = {
            "stroke": self.stroke,
            "stroke-width": f"{self.stroke_width}pt",
            "fill": self.fill,
            "opacity": str(self.opacity),
        }
        if self.stroke_opacity is not None:
            attrs["stroke-opacity"] = str(self.stroke_opacity)
        if self.fill_opacity is not None:
            attrs["fill-opacity"] = str(self.fill_opacity)
        return attrs


@dataclass
class Feature:
    """Represents a geographic feature extracted from OSM data.

    Attributes:
        geometry: List of (lon, lat) coordinate tuples
        tags: OSM tags dictionary
        is_closed: Whether the geometry forms a closed polygon
    """

    geometry: list[tuple[float, float]]
    tags: dict[str, str]
    is_closed: bool = False
