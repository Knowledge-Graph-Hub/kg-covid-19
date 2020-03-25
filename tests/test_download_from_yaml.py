import os
import tempfile
from unittest import TestCase, mock
from kg_emerging_viruses.utils import download_from_yaml


class TestDownloadFromYaml(TestCase):
    """Tests kg_emerging_viruses.download
    """

    @mock.patch('requests.get')
    def setUp(self, mock_get) -> None:
        self.mock_get = mock_get
        self.tempdir = tempfile.mkdtemp()
        download_from_yaml(yaml_file='resources/download.yaml', output_dir=self.tempdir)

    def test_request_call_args(self) -> None:
        # should call URL we specified in yaml
        self.assertTrue('https://test_url.org/test_1234.pdf' in self.mock_get.call_args[0])

    def test_requests_get_called(self) -> None:
        # should end up calling requests.get at some point
        self.assertTrue(self.mock_get.called)

    def test_output_files(self) -> None:
        # directory and downloaded file should exist
        self.assertTrue(os.path.exists(self.tempdir))
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, 'test_1234.pdf')))

    @mock.patch('requests.get')
    def test_different_local_name(self, mock_get) -> None:
        download_from_yaml(yaml_file='resources/download_diff_local_name.yaml',
                           output_dir=self.tempdir)
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, 'different.pdf')))
