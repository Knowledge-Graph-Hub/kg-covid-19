import os
import tempfile
from unittest import TestCase, mock

from kg_covid_19 import download
from kg_covid_19.utils.download_utils import download_from_api, download_from_yaml


class TestDownload(TestCase):
    """Tests kg_emerging_viruses.download
    """
    def setUp(self) -> None:
        pass

    # @mock.patch('requests.get')
    #def test_api_download(self):
    #    td = tempfile.gettempdir()
    #    download_from_yaml('tests/resources/download/download_api.yaml', td,
    #                       ignore_cache=True)

    # @mock.patch('requests.get')
    # def test_download(self, mock_get):
    #     dl_file = 'data/raw/test_1234.pdf'
    #     if os.path.exists(dl_file):
    #         os.unlink(dl_file)
    #     tmpdir = tempfile.mkdtemp()
    #     download(yaml_file='tests/resources/download.yaml', output_dir=tmpdir)
    #     self.assertTrue(mock_get.called)


