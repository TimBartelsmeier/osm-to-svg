"""Example 4: Comprehensive map with water, roads, railways, green spaces, and POI markers."""

from pathlib import Path

from osm_to_svg import Style, SvgMapper, features

# Set up directories relative to this script
script_dir = Path(__file__).parent
osmdata_dir = script_dir / "osmdata"
output_dir = script_dir / "output"
output_dir.mkdir(exist_ok=True)

# File paths
hannover_pbf = osmdata_dir / "hannover.osm.pbf"
marker_svg = script_dir / "poi marker.svg"
output_svg = output_dir / "advanced.svg"

# Bounding box for Hannover obtained from example_1_geocode_bbox.py
hannover_bbox = (9.68, 52.34, 9.79, 52.41)

# POI coordinates (latitude, longitude)
pois = [
    (52.3731, 9.7372),  # Kröpcke
    (52.3665, 9.7353),  # Landtag
    (52.3830, 9.7180),  # Leibniz University
]

# Render multiple layers
print("Rendering comprehensive map...")
with SvgMapper(str(hannover_pbf), bounds=hannover_bbox) as mapper:
    # Layer 1: Water bodies (filled blue shapes)
    print("  - Water bodies...")
    mapper.render_features(
        features=features.WATERWAYS.BODIES,
        style=Style(fill="#4A90E2"),
    )

    # Layer 2: Forests (dark green)
    print("  - Forests...")
    mapper.render_features(
        features=features.GREEN_SPACES.FORESTS,
        style=Style(fill="#046A04"),
    )

    # Layer 3: Parks and gardens (light green)
    print("  - Parks and gardens...")
    mapper.render_features(
        features=features.GREEN_SPACES.PARKS,
        style=Style(fill="#1FC21F"),
    )

    # Layer 4: Major roads (black)
    print("  - Major roads...")
    mapper.render_features(
        features=features.ROADS.MAJOR,
        style=Style(stroke="#000000", stroke_width=1),
    )

    # Layer 5: Local roads (grey)
    print("  - Local roads...")
    mapper.render_features(
        features=features.ROADS.LOCAL,
        style=Style(stroke="#5E5E5E", stroke_width=0.5),
    )

    # Layer 6: Railway tracks (orange)
    print("  - Railways...")
    mapper.render_features(
        features=features.RAILWAYS.ACTIVE,
        style=Style(stroke="#FF8C00", stroke_width=0.2),
    )

    # Layer 7: POI markers
    print("  - POI markers...")
    mapper.place_poi_markers(
        marker_svg_path=str(marker_svg),
        coords=pois,
        width_meters=500,
    )

    # Save all layers combined
    mapper.save_combined(str(output_svg))

print(f"Saved: {output_svg}")
