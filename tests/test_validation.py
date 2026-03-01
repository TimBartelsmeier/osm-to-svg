import pytest

from osm_to_svg.validation import validate_bbox


def test_validate_bbox_accepts_valid_values() -> None:
    bbox = (8.0, 52.0, 9.0, 53.0)
    assert validate_bbox(bbox) == bbox


@pytest.mark.parametrize(
    ("bbox", "error_fragment"),
    [
        ((-181.0, 0.0, 10.0, 10.0), "Invalid longitude"),
        ((0.0, -91.0, 10.0, 10.0), "Invalid latitude"),
        ((10.0, 0.0, 9.0, 10.0), "min_lon"),
        ((0.0, 10.0, 10.0, 9.0), "min_lat"),
    ],
)
def test_validate_bbox_rejects_invalid_ranges(
    bbox: tuple[float, float, float, float],
    error_fragment: str,
) -> None:
    with pytest.raises(ValueError, match=error_fragment):
        validate_bbox(bbox)
