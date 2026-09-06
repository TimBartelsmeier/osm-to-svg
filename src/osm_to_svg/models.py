"""Data models for styling and feature representation."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, TypeAlias

from pydantic import BaseModel, Field, model_validator

if TYPE_CHECKING:
    from osm_to_svg.features import FeatureSpec

MarkerAnchor = Literal[
    "top",
    "top-right",
    "right",
    "bottom-right",
    "bottom",
    "bottom-left",
    "left",
    "top-left",
    "center",
]
OsmObjectType = Literal["node", "way", "relation"]
BoundingBox: TypeAlias = tuple[float, float, float, float]


@dataclass(frozen=True)
class OsmObjectId:
    """Typed identity of an OpenStreetMap object."""

    object_type: OsmObjectType
    object_id: int

    def __post_init__(self) -> None:
        if self.object_id <= 0:
            raise ValueError("OSM object ID must be greater than 0")

    def __str__(self) -> str:
        return f"{self.object_type}/{self.object_id}"


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


class PoiStyle(BaseModel):
    """Style/configuration for placing POI markers.

    Exactly one sizing method must be provided: `scale`, `width_meters`, or
    `height_meters`. This is enforced by the model validator and raises
    ValueError when zero or multiple sizing methods are configured.
    """

    marker_svg_path: str = Field(description="Path to SVG file used as marker")
    scale: float | None = Field(
        default=None,
        gt=0,
        description="Scale factor for marker size relative to marker SVG dimensions",
    )
    anchor: MarkerAnchor = Field(
        default="center",
        description="Anchor point of the marker aligned to each POI coordinate",
    )
    width_meters: float | None = Field(
        default=None,
        gt=0,
        description="Target marker width in meters",
    )
    height_meters: float | None = Field(
        default=None,
        gt=0,
        description="Target marker height in meters",
    )

    @model_validator(mode="after")
    def _validate_single_sizing_method(self) -> "PoiStyle":
        """Ensure exactly one sizing method is configured."""
        sizing_methods = sum(
            [
                self.scale is not None,
                self.width_meters is not None,
                self.height_meters is not None,
            ]
        )
        if sizing_methods == 0:
            raise ValueError(
                "Must specify either scale, width_meters, or height_meters"
            )
        if sizing_methods > 1:
            raise ValueError(
                "Cannot specify multiple sizing methods (scale, width_meters, height_meters)"
            )
        return self


@dataclass
class Feature:
    """Represents a geographic feature extracted from OSM data.

    Attributes:
        geometry: List of (lat, lon) coordinate tuples
        tags: OSM tags dictionary
        is_closed: Whether the geometry forms a closed polygon
    """

    geometry: list[tuple[float, float]]
    tags: dict[str, str]
    is_closed: bool = False
    object_id: OsmObjectId | None = None


@dataclass
class FeatureLayer:
    """A styled feature specification with an optional selection limit."""

    features: "FeatureSpec"
    style: Style
    layer_id: str | None = None
    bboxes: Sequence[BoundingBox] | None = None
    object_ids: Iterable[OsmObjectId] | None = None

    def __post_init__(self) -> None:
        from osm_to_svg.validation import validate_bbox

        if self.bboxes is not None:
            if not self.bboxes:
                raise ValueError("bboxes must not be empty")
            self.bboxes = tuple(validate_bbox(box) for box in self.bboxes)
        if self.bboxes is not None and self.object_ids is not None:
            raise ValueError("Specify either bboxes or object_ids, not both")
        if self.object_ids is not None:
            self.object_ids = frozenset(self.object_ids)
            if not self.object_ids:
                raise ValueError("object_ids must not be empty")
