"""Coordinate transformation between WGS84 (lat/lon) and SVG coordinates."""

import math

from pyproj import Transformer

from osm_to_svg.validation import validate_bbox


class CoordinateTransformer:
    """Handles coordinate transformation from WGS84 to SVG coordinates.

    Uses Web Mercator projection (EPSG:3857) to convert geographic coordinates
    to a projected system, then maps to SVG pixel coordinates. The output SVG
    dimensions are calculated based on a specified scale (e.g., 1:100,000) and DPI.

    For regions with Mercator projection distortion, the scale is accurate at the
    center latitude of the bounding box, with distortion increasing toward the edges.
    """

    def __init__(
        self,
        bounds: tuple[float, float, float, float],
        scale: int = 100000,
        dpi: int = 96,
    ):
        """Initialize coordinate transformer with geographic bounds.

        Args:
            bounds: Geographic bounding box as (south_lat, west_lon, north_lat, east_lon)
            scale: Map scale denominator (default: 100000 for 1:100,000).
                  At scale 1:100,000, 1km in reality = 1cm in output.
                  The scale is accurate at the center latitude.
            dpi: Dots per inch for the output SVG (default: 96)
        """
        if scale <= 0:
            raise ValueError("scale must be greater than 0")
        if dpi <= 0:
            raise ValueError("dpi must be greater than 0")

        self.geo_bounds = validate_bbox(bounds)
        self.scale = scale
        self.dpi = dpi

        # Create transformer from WGS84 (EPSG:4326) to Web Mercator (EPSG:3857)
        self.transformer = Transformer.from_crs(
            "EPSG:4326", "EPSG:3857", always_xy=True
        )

        # Project bounding box corners to get projected bounds
        south_lat, west_lon, north_lat, east_lon = self.geo_bounds

        min_x, min_y = self.transformer.transform(west_lon, south_lat)
        max_x, max_y = self.transformer.transform(east_lon, north_lat)

        # Store projected bounds
        self.proj_bounds = (min_x, min_y, max_x, max_y)
        self.proj_width = max_x - min_x
        self.proj_height = max_y - min_y

        # Calculate center latitude for Mercator scale correction
        center_lat = (south_lat + north_lat) / 2.0
        mercator_factor = math.cos(math.radians(center_lat))

        # Adjust projected dimensions to actual ground distance in meters
        # Web Mercator is in meters but distorted; apply correction at center latitude
        actual_width_m = self.proj_width * mercator_factor
        actual_height_m = self.proj_height * mercator_factor

        # Calculate pixels per meter based on scale and DPI
        # Formula: pixels/meter = dpi / (scale * inches/meter)
        # where inches/meter = meters_to_cm / cm_per_inch = 100 / 2.54 = 39.3701
        inches_per_meter = 100.0 / 2.54  # 100 cm/m divided by 2.54 cm/inch
        pixels_per_meter = self.dpi / (self.scale * (1.0 / inches_per_meter))

        # Calculate SVG dimensions from actual ground distance
        self.svg_width = max(1, int(actual_width_m * pixels_per_meter))
        self.svg_height = max(1, int(actual_height_m * pixels_per_meter))

        # Calculate scaling factors
        self.scale_x = self.svg_width / self.proj_width
        self.scale_y = self.svg_height / self.proj_height

    def latlon_to_svg(self, lat: float, lon: float) -> tuple[float, float]:
        """Convert geographic coordinates to SVG pixel coordinates.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees

        Returns:
            Tuple of (x, y) in SVG coordinate space
        """
        # Project to Web Mercator
        x_proj, y_proj = self.transformer.transform(lon, lat)

        # Transform to SVG space
        # Note: SVG y-axis grows downward, so we flip it
        min_x, min_y, max_x, max_y = self.proj_bounds

        x_svg = (x_proj - min_x) * self.scale_x
        y_svg = (max_y - y_proj) * self.scale_y  # Flip y-axis

        return (x_svg, y_svg)

    def get_viewbox(self) -> str:
        """Get SVG viewBox attribute value.

        Returns:
            ViewBox string in format "0 0 width height"
        """
        return f"0 0 {self.svg_width} {self.svg_height}"

    def get_dimensions(self) -> tuple[int, int]:
        """Get SVG dimensions.

        Returns:
            Tuple of (width, height) in pixels
        """
        return (self.svg_width, self.svg_height)

    def meters_to_pixels(self) -> tuple[float, float]:
        """Get conversion factors from meters to SVG pixels.

        Returns:
            Tuple of (pixels_per_meter_x, pixels_per_meter_y)
        """
        return (self.scale_x, self.scale_y)
