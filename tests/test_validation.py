import pytest

from osm_to_svg.models import BoundingBox
from osm_to_svg.validation import validate_bbox


def test_validate_bbox_accepts_valid_values() -> None:
    bbox = (52.0, 8.0, 53.0, 9.0)
    assert validate_bbox(bbox) == bbox


@pytest.mark.parametrize(
    ("bbox", "error_fragment"),
    [
        ((0.0, -181.0, 10.0, 10.0), "Invalid longitude"),
        ((-91.0, 0.0, 10.0, 10.0), "Invalid latitude"),
        ((10.0, 0.0, 9.0, 10.0), "south_lat"),
        ((0.0, 10.0, 10.0, 9.0), "west_lon"),
    ],
)
def test_validate_bbox_rejects_invalid_ranges(
    bbox: BoundingBox,
    error_fragment: str,
) -> None:
    with pytest.raises(ValueError, match=error_fragment):
        validate_bbox(bbox)
