import os
import tempfile
from unittest import TestCase, mock
from kg_emerging_viruses.utils import download_from_yaml


class TestRun(TestCase):
    """Tests kg_emerging_viruses.download
    """
    def setUp(self) -> None:
        pass

    @mock.patch('requests.get')
    def test_download_from_yaml(self, mock_get) -> None:
        dirpath = tempfile.mkdtemp()
        download_from_yaml(yaml_file='resources/download.yaml', output_dir=dirpath)

        # should call URL we specified in yaml
        self.assertTrue('https://test_url.org/test_1234.pdf' in mock_get.call_args[0])

        # should end up calling requests.get at some point
        self.assertTrue(mock_get.called)

        # directory and downloaded file should exist
        self.assertTrue(os.path.exists(dirpath))
        self.assertTrue(os.path.exists(os.path.join(dirpath, 'test_1234.pdf')))


