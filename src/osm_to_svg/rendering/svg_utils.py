"""Utility helpers for working with SVG marker fragments."""

import xml.etree.ElementTree as ET
from typing import Any

import svgwrite

__all__ = ["parse_svg_dimension", "copy_svg_element"]


def parse_svg_dimension(value: str | int | float, fallback: float = 24.0) -> float:
    """Parse an SVG dimension value (for example "24px" or "1.5pt") to float."""
    if isinstance(value, (int, float)):
        return float(value)

    normalized = str(value).replace("px", "").replace("pt", "").strip()
    try:
        return float(normalized)
    except ValueError:
        return fallback


def copy_svg_element(element: ET.Element, parent: Any, dwg: svgwrite.Drawing) -> None:
    """Recursively copy a subset of SVG XML tags into an svgwrite structure."""
    tag_name = element.tag.split("}")[-1]
    attrs = dict(element.attrib)

    if tag_name == "circle":
        parent.add(
            dwg.circle(
                center=(attrs.get("cx", 0), attrs.get("cy", 0)),
                r=attrs.get("r", 0),
                **_without_keys(attrs, "cx", "cy", "r"),
            )
        )
    elif tag_name == "rect":
        parent.add(
            dwg.rect(
                insert=(attrs.get("x", 0), attrs.get("y", 0)),
                size=(attrs.get("width", 0), attrs.get("height", 0)),
                **_without_keys(attrs, "x", "y", "width", "height"),
            )
        )
    elif tag_name == "path":
        parent.add(dwg.path(d=attrs.get("d", ""), **_without_keys(attrs, "d")))
    elif tag_name == "line":
        parent.add(
            dwg.line(
                start=(attrs.get("x1", 0), attrs.get("y1", 0)),
                end=(attrs.get("x2", 0), attrs.get("y2", 0)),
                **_without_keys(attrs, "x1", "y1", "x2", "y2"),
            )
        )
    elif tag_name == "polyline":
        parent.add(
            dwg.polyline(
                points=_parse_points(attrs.get("points", "")),
                **_without_keys(attrs, "points"),
            )
        )
    elif tag_name == "polygon":
        parent.add(
            dwg.polygon(
                points=_parse_points(attrs.get("points", "")),
                **_without_keys(attrs, "points"),
            )
        )
    elif tag_name == "ellipse":
        parent.add(
            dwg.ellipse(
                center=(attrs.get("cx", 0), attrs.get("cy", 0)),
                r=(attrs.get("rx", 0), attrs.get("ry", 0)),
                **_without_keys(attrs, "cx", "cy", "rx", "ry"),
            )
        )
    elif tag_name == "g":
        group = dwg.g(**attrs)
        for child in element:
            copy_svg_element(child, group, dwg)
        parent.add(group)


def _without_keys(attrs: dict[str, str], *keys: str) -> dict[str, str]:
    excluded = set(keys)
    return {k: v for k, v in attrs.items() if k not in excluded}


def _parse_points(raw_points: str) -> list[tuple[float, float]]:
    values = raw_points.replace(",", " ").split()
    if len(values) < 2:
        return []

    points: list[tuple[float, float]] = []
    for i in range(0, len(values) - 1, 2):
        try:
            points.append((float(values[i]), float(values[i + 1])))
        except ValueError:
            continue
    return points
