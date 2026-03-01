"""Example 1: Get bounding box for a region centered on Hannover using geocoding."""

from osm_to_svg import get_bbox_from_place

# Get bounding box for a 7.5km width by 7.5km height region centered on Hannover
print("Geocoding 'Hannover, Germany' and creating bounding box...")
print("  - Width: 7.5 km")
print("  - Height: 7.5 km")

hannover_bbox = get_bbox_from_place(
    "Hannover, Germany",
    width_km=7.5,
    height_km=7.5,
)

print("\nResult:")
print(f"  Bounding box: {hannover_bbox}")
print("  (min_lon, min_lat, max_lon, max_lat)")
