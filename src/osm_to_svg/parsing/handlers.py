"""osmium handlers used by PBF parsing."""

import osmium

from osm_to_svg.features import FeatureSpec
from osm_to_svg.models import BoundingBox, Feature, OsmObjectId


class BoundsHandler(osmium.SimpleHandler):
    """Handler to extract geographic bounds from a PBF file."""

    def __init__(self):
        """Initialize the handler with infinite sentinel bounds."""
        super().__init__()
        self.south_lat = float("inf")
        self.west_lon = float("inf")
        self.north_lat = float("-inf")
        self.east_lon = float("-inf")

    def node(self, node):
        """Update the running min/max bounds from a valid node location."""
        if node.location.valid():
            lat = node.location.lat
            lon = node.location.lon
            self.south_lat = min(self.south_lat, lat)
            self.west_lon = min(self.west_lon, lon)
            self.north_lat = max(self.north_lat, lat)
            self.east_lon = max(self.east_lon, lon)

    def get_bounds(self) -> BoundingBox:
        """Return the accumulated bounding box as ``(south_lat, west_lon, north_lat, east_lon)``."""
        return (self.south_lat, self.west_lon, self.north_lat, self.east_lon)


class FeatureHandler(osmium.SimpleHandler):
    """Handler to extract specific features from a PBF file."""

    def __init__(self, spec: FeatureSpec):
        """Initialize the handler with the feature specification to match against."""
        super().__init__()
        self.features: list[Feature] = []
        self.match_clauses = spec.match_clauses
        self.node_cache: dict[int, tuple[float, float]] = {}

    def node(self, node):
        """Cache valid node locations for later way geometry resolution."""
        if node.location.valid():
            self.node_cache[node.id] = (node.location.lat, node.location.lon)

    def way(self, way):
        """Extract a way as a Feature if its tags match the spec."""
        tags = {tag.k: tag.v for tag in way.tags}
        if not self._matches_filter(tags):
            return

        geometry = []
        for node in way.nodes:
            if node.ref in self.node_cache:
                geometry.append(self.node_cache[node.ref])

        if len(geometry) < 2:
            return

        is_closed = len(geometry) >= 4 and geometry[0] == geometry[-1]
        object_id = getattr(way, "id", None)
        self.features.append(
            Feature(
                geometry=geometry,
                tags=tags,
                is_closed=is_closed,
                object_id=OsmObjectId("way", object_id)
                if object_id is not None
                else None,
            )
        )

    def area(self, area):
        """Extract the outer ring of an area as a closed Feature if its tags match the spec."""
        tags = {tag.k: tag.v for tag in area.tags}
        if not self._matches_filter(tags):
            return

        try:
            outer_ring = list(area.outer_rings())[0]
            geometry = [(node.lat, node.lon) for node in outer_ring]
            if len(geometry) >= 4:
                is_relation = getattr(area, "is_relation", lambda: False)()
                object_type = "relation" if is_relation else "way"
                original_id = getattr(area, "orig_id", lambda: 0)()
                self.features.append(
                    Feature(
                        geometry=geometry,
                        tags=tags,
                        is_closed=True,
                        object_id=OsmObjectId(object_type, original_id)
                        if original_id > 0
                        else None,
                    )
                )
        except (IndexError, RuntimeError):
            pass

    def _matches_filter(self, tags: dict[str, str]) -> bool:
        """Return True if tags satisfy at least one configured match clause."""
        for clause in self.match_clauses:
            if all(
                tags.get(tag_key) in valid_values
                for tag_key, valid_values in clause.items()
            ):
                return True
        return False
