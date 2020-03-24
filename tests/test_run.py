from unittest import TestCase, skip
from click.testing import CliRunner
from mock import patch

import kg_emerging_viruses

from run import transform
from run import download


class TestRun(TestCase):
    """Tests the run.py script."""
    def setUp(self) -> None:
        self.runner = CliRunner()

    @skip
    def test_download(self):
        # TODO: I cannot for the life of me convince mock/patch to intercept call
        # to kg_download() in run.download()
        result = self.runner.invoke(cli=download,
                                    args=['-y', 'tests/resources/download.yaml'])
        self.assertTrue(kg_emerging_viruses.download.called, True)
        self.assertEqual(result.exit_code, 0)

    @skip
    def test_transform(self):
        # TODO: Likewise, need to mock/path kg_transform() in run.transform()
        result = self.runner.invoke(cli=transform,
                                    args=['-i', 'tests/data/raw'])
        self.assertTrue(kg_emerging_viruses.transform.called, True)
        self.assertEqual(result.exit_code, 0)

