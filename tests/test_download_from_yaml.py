import os
import tempfile
from unittest import TestCase, mock
from kg_covid_19.utils import download_from_yaml


class TestDownloadFromYaml(TestCase):
    """Tests download_yaml()
    """

    # @mock.patch('requests.get')
    # def setUp(self, mock_get) -> None:
    #     self.mock_get = mock_get
    #     self.tempdir = tempfile.mkdtemp()
    #     self.test_yaml_file = 'tests/resources/download.yaml'
    #     download_from_yaml(yaml_file=self.test_yaml_file, output_dir=self.tempdir)
    #
    # def test_request_call_args(self) -> None:
    #     # should call URL we specified in yaml
    #     self.assertTrue('https://test_url.org/test_1234.pdf' in self.mock_get.call_args[0])
    #
    # def test_requests_get_called(self) -> None:
    #     # should end up calling requests.get at some point
    #     self.assertTrue(self.mock_get.called)
    #
    # def test_output_files(self) -> None:
    #     # directory and downloaded file should exist
    #     self.assertTrue(os.path.exists(self.tempdir))
    #     self.assertTrue(os.path.exists(os.path.join(self.tempdir, 'test_1234.pdf')))
    #
    # @mock.patch('requests.get')
    # def test_different_local_name(self, mock_get) -> None:
    #     download_from_yaml(yaml_file='tests/resources/download_diff_local_name.yaml',
    #                        output_dir=self.tempdir)
    #     self.assertTrue(os.path.exists(os.path.join(self.tempdir, 'different.pdf')))
    #
    # @mock.patch('requests.get')
    # def test_ignore_cache_false(self, mock_get) -> None:
    #     self.mock_get = mock_get
    #     download_from_yaml(yaml_file=self.test_yaml_file,
    #                        output_dir=self.tempdir,
    #                        ignore_cache=True)
    #     self.assertTrue(self.mock_get.called)
    #
    # @mock.patch('requests.get')
    # def test_ignore_cache_true(self, mock_get) -> None:
    #     self.mock_get = mock_get
    #     download_from_yaml(yaml_file=self.test_yaml_file,
    #                        output_dir=self.tempdir,
    #                        ignore_cache=False)
    #     self.assertTrue(not self.mock_get.called)
