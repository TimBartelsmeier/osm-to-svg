"""osmium handlers used by PBF parsing."""

import osmium

from osm_to_svg.features import FeatureSpec
from osm_to_svg.models import Feature


class BoundsHandler(osmium.SimpleHandler):
    """Handler to extract geographic bounds from a PBF file."""

    def __init__(self):
        super().__init__()
        self.min_lon = float("inf")
        self.min_lat = float("inf")
        self.max_lon = float("-inf")
        self.max_lat = float("-inf")

    def node(self, node):
        if node.location.valid():
            lon = node.location.lon
            lat = node.location.lat
            self.min_lon = min(self.min_lon, lon)
            self.min_lat = min(self.min_lat, lat)
            self.max_lon = max(self.max_lon, lon)
            self.max_lat = max(self.max_lat, lat)

    def get_bounds(self) -> tuple[float, float, float, float]:
        return (self.min_lon, self.min_lat, self.max_lon, self.max_lat)


class FeatureHandler(osmium.SimpleHandler):
    """Handler to extract specific features from a PBF file."""

    def __init__(self, spec: FeatureSpec):
        super().__init__()
        self.features: list[Feature] = []
        self.tag_filters = spec.tag_filters
        self.node_cache: dict[int, tuple[float, float]] = {}

    def node(self, node):
        if node.location.valid():
            self.node_cache[node.id] = (node.location.lon, node.location.lat)

    def way(self, way):
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
        self.features.append(Feature(geometry=geometry, tags=tags, is_closed=is_closed))

    def area(self, area):
        tags = {tag.k: tag.v for tag in area.tags}
        if not self._matches_filter(tags):
            return

        try:
            outer_ring = list(area.outer_rings())[0]
            geometry = [(node.lon, node.lat) for node in outer_ring]
            if len(geometry) >= 4:
                self.features.append(
                    Feature(geometry=geometry, tags=tags, is_closed=True)
                )
        except (IndexError, RuntimeError):
            pass

    def _matches_filter(self, tags: dict[str, str]) -> bool:
        for tag_key, valid_values in self.tag_filters.items():
            if tag_key in tags and tags[tag_key] in valid_values:
                return True
        return False
