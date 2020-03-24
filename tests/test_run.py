from unittest import TestCase, skip
from click.testing import CliRunner

import kg_emerging_viruses

from run import transform
from run import download


class TestRun(TestCase):
    """Tests the run.py script."""
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_download(self):
        result = self.runner.invoke(cli=download,
                                    args=['-y', 'tests/resources/download.yaml'])
        self.assertEqual(result.exit_code, 0)

    @skip
    def test_transform(self):
        result = self.runner.invoke(cli=transform,
                                    args=['-i', 'tests/data/raw'])
        self.assertEqual(result.exit_code, 0)

