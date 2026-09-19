"""Utility helpers for working with SVG marker fragments."""

import re
import xml.etree.ElementTree as ET
from typing import Any

import svgwrite

__all__ = ["copy_svg_element", "parse_svg_dimension"]


def parse_svg_dimension(value: str | float, fallback: float = 24.0) -> float:
    """Parse an SVG dimension into CSS pixels, using ``fallback`` for unsupported units."""
    if isinstance(value, (int, float)):
        return float(value)

    match = re.fullmatch(r"\s*([+-]?\d*\.?\d+)(px|pt|mm|cm|in)?\s*", str(value))
    if match is None:
        return fallback
    number = float(match.group(1))
    unit = match.group(2) or "px"
    factors = {"px": 1.0, "pt": 96 / 72, "mm": 96 / 25.4, "cm": 96 / 2.54, "in": 96}
    return number * factors[unit]


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
    """Return a copy of attrs with the specified keys removed."""
    excluded = set(keys)
    return {k: v for k, v in attrs.items() if k not in excluded}


def _parse_points(raw_points: str) -> list[tuple[float, float]]:
    """Parse an SVG ``points`` attribute string into a list of (x, y) float tuples."""
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
