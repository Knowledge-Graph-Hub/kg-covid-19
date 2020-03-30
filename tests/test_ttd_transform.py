import types
from unittest import TestCase

from kg_covid_19.transform_utils.ttd.ttd import TTDTransform


class TestTTD(TestCase):
    """Tests the ttd transform"""

    def setUp(self) -> None:
        self.ttd_dl_snippet = "tests/resources/P1-01-TTD_target_download_SNIPPET.txt"
        self.ttd = TTDTransform()

    def test_parse_ttd_file(self) -> None:
        self.assertTrue(isinstance(getattr(self.ttd, "parse_ttd_file"),
                                   types.MethodType))
        parse_result = self.ttd.parse_ttd_file(self.ttd_dl_snippet)
        self.assertTrue(isinstance(parse_result, dict))

    def test_run(self) -> None:
        self.assertTrue(isinstance(getattr(self.ttd, "run"), types.MethodType))

