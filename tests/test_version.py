from kg_covid_19.__version__ import __version__
from validate_version_code import validate_version_code


def test_version():
    """Tests the package version."""

    assert validate_version_code(__version__)

    return None
