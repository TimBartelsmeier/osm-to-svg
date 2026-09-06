"""Example 1: Geocode a place name and create a bounding box around it."""

from osm_to_svg import geocode_coordinates, get_bbox_around_coordinates

# Step 1: Geocode the place name to get its coordinates
print("Geocoding 'Hannover, Germany'...")
lat, lon = geocode_coordinates("Hannover, Germany")
print(f"  Coordinates: lat={lat}, lon={lon}")

# Step 2: Compute a bounding box around those coordinates
print("\nBuilding 7.5 km × 7.5 km bounding box...")
hannover_bbox = get_bbox_around_coordinates(
    lat,
    lon,
    width_km=7.5,
    height_km=7.5,
)

print("\nResult:")
print(f"  Bounding box: {hannover_bbox}")
print("  (min_lon, min_lat, max_lon, max_lat)")
