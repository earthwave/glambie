import pytest
from glambie.util.version_helpers import get_glambie_bucket_name


@pytest.mark.parametrize(
    ("version", "expected_bucket_name"),
    [
        (1, "glambie-submissions"),
        (2, "glambie2-submissions"),
    ],
)
def test_get_glambie_bucket_name(version, expected_bucket_name):
    assert get_glambie_bucket_name(version) == expected_bucket_name


def test_get_glambie_bucket_name_invalid_version():
    with pytest.raises(ValueError, match="Invalid glambie_version: 3"):
        get_glambie_bucket_name(3)
