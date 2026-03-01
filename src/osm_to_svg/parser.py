"""PBF file parser using osmium."""

from enum import Enum

import osmium

from osm_to_svg.features import (
    BuildingType,
    WaterwayType,
    get_osm_filter,
)
from osm_to_svg.models import Feature


class BoundsHandler(osmium.SimpleHandler):
    """Handler to extract geographic bounds from a PBF file."""

    def __init__(self):
        """Initialize bounds accumulator with infinite min/max sentinels."""
        super().__init__()
        self.min_lon = float("inf")
        self.min_lat = float("inf")
        self.max_lon = float("-inf")
        self.max_lat = float("-inf")

    def node(self, node):
        """Process each node to update bounds."""
        if node.location.valid():
            lon = node.location.lon
            lat = node.location.lat
            self.min_lon = min(self.min_lon, lon)
            self.min_lat = min(self.min_lat, lat)
            self.max_lon = max(self.max_lon, lon)
            self.max_lat = max(self.max_lat, lat)

    def get_bounds(self) -> tuple[float, float, float, float]:
        """Get the computed bounds.

        Returns:
            Tuple of (min_lon, min_lat, max_lon, max_lat)
        """
        return (self.min_lon, self.min_lat, self.max_lon, self.max_lat)


class FeatureHandler(osmium.SimpleHandler):
    """Handler to extract specific features from a PBF file."""

    def __init__(
        self,
        feature_type: type[Enum],
        subtypes: list[Enum] | None = None,
    ):
        """Initialize feature extraction handler.

        Args:
            feature_type: Feature enum class to filter for.
            subtypes: Optional subset of enum values to include.
        """
        super().__init__()
        self.feature_type = feature_type
        self.features: list[Feature] = []

        # Get OSM tag filters
        self.tag_filters = get_osm_filter(feature_type, subtypes)

        # Cache for node locations (needed to resolve way geometries)
        self.node_cache: dict[int, tuple[float, float]] = {}

    def node(self, node):
        """Cache node locations for later way processing."""
        if node.location.valid():
            self.node_cache[node.id] = (node.location.lon, node.location.lat)

    def way(self, way):
        """Process ways that match our feature filters."""
        # Check if this way has tags we're interested in
        tags = {tag.k: tag.v for tag in way.tags}

        if not self._matches_filter(tags):
            return

        # Extract geometry
        geometry = []
        for node in way.nodes:
            if node.ref in self.node_cache:
                geometry.append(self.node_cache[node.ref])

        if len(geometry) < 2:
            # Skip invalid geometries
            return

        # Check if way is closed (forms a polygon)
        is_closed = len(geometry) >= 4 and geometry[0] == geometry[-1]

        self.features.append(Feature(geometry=geometry, tags=tags, is_closed=is_closed))

    def area(self, area):
        """Process areas (multipolygons) that match our feature filters."""
        tags = {tag.k: tag.v for tag in area.tags}

        if not self._matches_filter(tags):
            return

        # Extract outer ring geometry
        try:
            outer_ring = list(area.outer_rings())[0]
            geometry = [(node.lon, node.lat) for node in outer_ring]

            if len(geometry) >= 4:
                self.features.append(
                    Feature(geometry=geometry, tags=tags, is_closed=True)
                )
        except (IndexError, RuntimeError):
            # Skip if we can't extract geometry
            pass

    def _matches_filter(self, tags: dict[str, str]) -> bool:
        """Check if tags match our filters."""
        for tag_key, valid_values in self.tag_filters.items():
            if tag_key in tags and tags[tag_key] in valid_values:
                return True

        # Special handling for waterways: also check natural=water with water type
        if self.feature_type == WaterwayType:
            if "natural" in tags and tags["natural"] == "water":
                # Accept any water body
                return True
            if "natural" in tags and tags["natural"] == "coastline":
                return True

        return False


class PBFParser:
    """Parser for OpenStreetMap PBF files."""

    def __init__(self, pbf_path: str):
        """Initialize parser with path to PBF file.

        Args:
            pbf_path: Path to the PBF file
        """
        self.pbf_path = pbf_path

    def get_bounds(self) -> tuple[float, float, float, float]:
        """Extract geographic bounds from the PBF file.

        Returns:
            Tuple of (min_lon, min_lat, max_lon, max_lat)
        """
        handler = BoundsHandler()
        handler.apply_file(self.pbf_path, locations=True)
        return handler.get_bounds()

    def extract_features(
        self,
        feature_type: type[Enum],
        subtypes: list[Enum] | None = None,
    ) -> list[Feature]:
        """Extract features of a specific type from the PBF file.

        Args:
            feature_type: Type of features to extract (RoadType, RailwayType, etc.)
            subtypes: Optional list of specific subtypes to extract

        Returns:
            List of Feature objects
        """
        handler = FeatureHandler(feature_type, subtypes)

        # First pass: cache all node locations
        handler.apply_file(self.pbf_path, locations=True)

        # Second pass: extract ways and areas with features
        if feature_type == BuildingType or feature_type == WaterwayType:
            # Buildings and some waterways might be areas (multipolygons)
            handler.apply_file(self.pbf_path, locations=True, idx="flex_mem")

        # Deduplicate features because multi-pass extraction can revisit
        # matching ways when area processing is enabled.
        unique_features: list[Feature] = []
        seen: set[
            tuple[tuple[tuple[float, float], ...], tuple[tuple[str, str], ...], bool]
        ] = set()

        for feature in handler.features:
            key = (
                tuple(feature.geometry),
                tuple(sorted(feature.tags.items())),
                feature.is_closed,
            )
            if key not in seen:
                seen.add(key)
                unique_features.append(feature)

        return unique_features
