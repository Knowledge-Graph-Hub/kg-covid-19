import os

from kg_emerging_viruses import download, transform


def test_run():
    """Tests the run.py script."""

    download('tests/resources/download.yaml', 'tests/data/raw')

    return None
