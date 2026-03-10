"""SVG file combiner for layering multiple SVG files."""

import xml.etree.ElementTree as ET


def _create_root_with_boundary_clip(
    width: str | None,
    height: str | None,
    viewbox: str | None,
) -> ET.Element:
    """Create a root ``<svg>`` element with a ``boundary-clip`` clipPath in its defs."""
    if viewbox is None:
        raise ValueError("viewBox is required for combining SVG layers")

    svg_ns = "http://www.w3.org/2000/svg"
    ET.register_namespace("", svg_ns)

    combined_root = ET.Element(
        f"{{{svg_ns}}}svg",
        attrib={
            "width": width,
            "height": height,
            "viewBox": viewbox,
        },
    )

    vb_parts = viewbox.split()
    vb_x, vb_y, vb_width, vb_height = vb_parts

    defs = ET.Element(f"{{{svg_ns}}}defs")
    clip_path = ET.Element(f"{{{svg_ns}}}clipPath", attrib={"id": "boundary-clip"})
    clip_rect = ET.Element(
        f"{{{svg_ns}}}rect",
        attrib={
            "x": vb_x,
            "y": vb_y,
            "width": vb_width,
            "height": vb_height,
        },
    )
    clip_path.append(clip_rect)
    defs.append(clip_path)
    combined_root.append(defs)
    return combined_root


def _append_layer_from_source(
    source_root: ET.Element,
    combined_root: ET.Element,
    viewbox: str,
    layer_id: str,
    source_name: str,
) -> None:
    """Append the visible children of source_root as a named layer group to combined_root."""
    if source_root.get("viewBox") != viewbox:
        raise ValueError(
            f"{source_name} has inconsistent viewBox. "
            f"Expected {viewbox}, got {source_root.get('viewBox')}"
        )

    svg_ns = "http://www.w3.org/2000/svg"
    layer_group = ET.Element(
        f"{{{svg_ns}}}g",
        attrib={
            "id": layer_id,
            "clip-path": "url(#boundary-clip)",
        },
    )

    for child in source_root:
        tag_name = child.tag.split("}")[-1]
        if tag_name in ["title", "desc", "metadata", "defs"]:
            continue
        layer_group.append(child)

    combined_root.append(layer_group)


def combine_elements(
    elements: list[ET.Element], output_path: str, background_color: str | None = None
) -> None:
    """Combine multiple SVG ``<svg>`` elements into a single layered SVG file.

    All elements must share the same ``viewBox``. They are stacked in the order
    given (first element = bottom layer). An optional solid background rectangle
    is inserted before any layers when ``background_color`` is provided.

    Args:
        elements: Non-empty list of SVG root elements to combine.
        output_path: Destination file path for the combined SVG.
        background_color: Optional fill color for a full-canvas background rectangle.

    Raises:
        ValueError: If ``elements`` is empty or the viewBoxes are inconsistent.
    """
    if not elements:
        raise ValueError("elements cannot be empty")

    first_root = elements[0]
    width = first_root.get("width")
    height = first_root.get("height")
    viewbox = first_root.get("viewBox")

    combined_root = _create_root_with_boundary_clip(width, height, viewbox)

    vb_parts = viewbox.split()
    vb_x, vb_y, vb_width, vb_height = vb_parts

    svg_ns = "http://www.w3.org/2000/svg"

    if background_color:
        background = ET.Element(
            f"{{{svg_ns}}}rect",
            attrib={
                "x": vb_x,
                "y": vb_y,
                "width": vb_width,
                "height": vb_height,
                "fill": background_color,
            },
        )
        combined_root.append(background)

    for idx, root in enumerate(elements):
        _append_layer_from_source(
            source_root=root,
            combined_root=combined_root,
            viewbox=viewbox,
            layer_id=f"layer-{idx}",
            source_name=f"Element {idx}",
        )

    tree = ET.ElementTree(combined_root)
    ET.indent(tree, space="  ")
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
