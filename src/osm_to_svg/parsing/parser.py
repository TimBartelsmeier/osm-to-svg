"""PBF parser facade."""

from osm_to_svg.features import FeatureSpec
from osm_to_svg.models import Feature
from osm_to_svg.parsing.handlers import BoundsHandler, FeatureHandler


class PBFParser:
    """Parser for OpenStreetMap PBF files."""

    def __init__(self, pbf_path: str):
        """Initialize the parser with the path to a PBF file."""
        self.pbf_path = pbf_path

    def get_bounds(self) -> tuple[float, float, float, float]:
        """Scan all nodes in the PBF file and return the geographic bounding box.

        Returns:
            Bounding box as ``(south_lat, west_lon, north_lat, east_lon)``.
        """
        handler = BoundsHandler()
        handler.apply_file(self.pbf_path, locations=True)
        return handler.get_bounds()

    def extract_features(self, spec: FeatureSpec) -> list[Feature]:
        """Extract OSM features matching the given spec from the PBF file.

        Deduplicates the results so each unique geometry appears only once.
        If ``spec.needs_areas`` is True, the file is processed a second time
        with area indexing enabled to capture multipolygon relations.

        Args:
            spec: Feature specification describing the OSM tag filters.

        Returns:
            List of unique :class:`~osm_to_svg.models.Feature` objects.
        """
        handler = FeatureHandler(spec)
        handler.apply_file(self.pbf_path, locations=True)

        if spec.needs_areas:
            handler.apply_file(self.pbf_path, locations=True, idx="flex_mem")

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
