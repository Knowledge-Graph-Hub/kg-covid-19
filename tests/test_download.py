from unittest import TestCase, mock
from kg_covid_19 import download


class TestDownload(TestCase):
    """Tests kg_emerging_viruses.download
    """
    def setUp(self) -> None:
        pass

    @mock.patch('requests.get')
    def test_download(self, mock_get):
        download(yaml_file='tests/resources/download.yaml', output_dir="fakedir")
        self.assertTrue(mock_get.called)


