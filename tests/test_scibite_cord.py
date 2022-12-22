"""Tests for parsing Scibite CORD data."""

import tempfile
from unittest import TestCase

from kg_covid_19.transform_utils.scibite_cord import ScibiteCordTransform


class TestScibiteCord(TestCase):
    """Test for parsing Scibite CORD data."""

    def setUp(self) -> None:
        """Set up the test class."""
        self.input_dir = "tests/resources/scibite_cord"
        self.output_dir = "tests/resources/scibite_cord"
        self.tmpdir = tempfile.TemporaryDirectory(dir=self.input_dir)
        self.scibite = ScibiteCordTransform(
            input_dir=self.input_dir, output_dir=self.tmpdir.name
        )

    def test_run(self):
        """Test running the scibite transformation."""
        self.scibite.run()
