"""Example 5: Render all buildings and all roads.

Note: This example renders ALL building and road types in the bounding box,
which can result in very large SVG files (potentially 10+ MB) depending on
the area size and density of features. Processing time may also be significant.
Consider using a smaller bounding box or specific subtypes for production use.
"""

from pathlib import Path

from osm_to_svg import BuildingType, RoadType, Style, SvgMapper

# Set up directories relative to this script
script_dir = Path(__file__).parent
osmdata_dir = script_dir / "osmdata"
output_dir = script_dir / "output"
output_dir.mkdir(exist_ok=True)

# File paths
hannover_pbf = osmdata_dir / "hannover.osm.pbf"
output_svg = output_dir / "all_buildings_roads.svg"

# Bounding box for Hannover obtained from example_1_geocode_bbox.py
hannover_bbox = (9.68, 52.34, 9.79, 52.41)

# Render all buildings and roads
print("Rendering all buildings and roads...")
print("⚠️  Warning: This may take a while and produce a large file.")

with SvgMapper(
    str(hannover_pbf), bounds=hannover_bbox, background_color="#FFFFFF"
) as mapper:
    # Layer 1: All buildings (filled grey shapes)
    print("  - All buildings...")
    mapper.render_features(
        feature_type=BuildingType,
        subtypes=None,  # None = render ALL building types
        style=Style(fill="#925000"),
    )

    # Layer 2: All roads (black lines)
    print("  - All roads...")
    mapper.render_features(
        feature_type=RoadType,
        subtypes=None,  # None = render ALL road types
        style=Style(stroke="#000000", stroke_width=0.25),
    )

    # Save combined layers
    mapper.save_combined(str(output_svg))

print(f"Saved: {output_svg}")
