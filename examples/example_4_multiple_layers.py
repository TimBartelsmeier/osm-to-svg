"""Example 4: Comprehensive map with water, roads, railways, green spaces, and POI markers."""

from pathlib import Path

from osm_to_svg import PoiStyle, Style, create_map, features

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
hannover_bbox = (52.34, 9.68, 52.41, 9.79)

# POI coordinates (latitude, longitude)
pois = [
    (52.3731, 9.7372),  # Kröpcke
    (52.3665, 9.7353),  # Landtag
    (52.3830, 9.7180),  # Leibniz University
]

# Render multiple layers
print("Rendering comprehensive map:")
print("  - Water bodies")
print("  - Forests")
print("  - Parks and gardens")
print("  - Major roads")
print("  - Local roads")
print("  - Railways")
print("  - POI markers")
print("This may take some time...")
print()
create_map(
    pbf_path=str(hannover_pbf),
    bounds=hannover_bbox,
    feature_layers=[
        (features.WATER.BODIES, Style(fill="#4A90E2")),
        (features.GREEN_SPACES.FORESTS, Style(fill="#046A04")),
        (features.GREEN_SPACES.PARKS, Style(fill="#1FC21F")),
        (features.ROADS.MAJOR, Style(stroke="#000000", stroke_width=1)),
        (features.ROADS.LOCAL, Style(stroke="#5E5E5E", stroke_width=0.5)),
        (features.RAILWAYS.ACTIVE, Style(stroke="#FF8C00", stroke_width=0.2)),
    ],
    poi_layers=[
        (
            pois,
            PoiStyle(
                marker_svg_path=str(marker_svg),
                width_meters=500,
            ),
        )
    ],
    output_path=str(output_svg),
    show_progress=True,
)

print()
print(f"Saved: {output_svg}")
