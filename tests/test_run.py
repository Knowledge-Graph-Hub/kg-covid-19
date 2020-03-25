import requests
import kg_emerging_viruses

from unittest import TestCase, skip
from click.testing import CliRunner
from unittest import mock
from kg_emerging_viruses import download

from run import transform
from run import download
from tests.resources.mock_download import mocked_requests_get


class TestRun(TestCase):
    """Tests the run.py script."""
    def setUp(self) -> None:
        self.runner = CliRunner()

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_download(self, mock_get):
        result = self.runner.invoke(cli=download,
                                    args=['-y', 'resources/download.yaml'])
        # this really just makes sure request.get get called somewhere downstream
        self.assertTrue(mock_get.called)

    @skip
    def test_transform(self):
        result = self.runner.invoke(cli=transform,
                                    args=['-i', 'data/raw'])
        self.assertEqual(result.exit_code, 0)

