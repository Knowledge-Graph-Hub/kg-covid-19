import types
from unittest import TestCase
from parameterized import parameterized
from kg_covid_19.transform_utils.ttd.ttd import TTDTransform


class TestTTD(TestCase):
    """Tests the ttd transform"""

    def setUp(self) -> None:
        self.ttd_dl_snippet = "tests/resources/P1-01-TTD_target_download_SNIPPET.txt"
        self.ttd_dl_mult_ids = "tests/resources/P1-01-TTD_target_download_MULTIPLE_IDS.txt"
        self.ttd = TTDTransform()
        self.abbreviations = \
        ['TARGETID', 'FORMERID', 'UNIPROID', 'TARGNAME', 'GENENAME', 'TARGTYPE',
         'SYNONYMS', 'FUNCTION', 'PDBSTRUC', 'BIOCLASS', 'ECNUMBER', 'SEQUENCE',
         'DRUGINFO', 'KEGGPATH', 'WIKIPATH', 'WHIZPATH', 'REACPATH', 'NET_PATH',
         'INTEPATH', 'PANTPATH', 'BIOCPATH']

    def test_parse_ttd_file_fxn(self) -> None:
        self.assertTrue(isinstance(getattr(self.ttd, "parse_ttd_file"),
                                   types.MethodType))
        parsed_result = self.ttd.parse_ttd_file(self.ttd_dl_snippet)
        self.assertTrue(isinstance(parsed_result, dict))
        self.assertCountEqual(parsed_result.keys(), ["T47101", "T17514"])
        self.assertTrue(set(parsed_result["T47101"].keys()) <= set(self.abbreviations))

    @parameterized.expand([
        ['T47101', 'TARGETID', ['T47101']],
        ['T47101', 'GENENAME', ['FGFR1']],
        ['T47101', 'DRUGINFO', [['D09HNV', 'Intedanib', 'Approved'],
                                ['D01PZD', 'Romiplostim', 'Approved']]],
        ['T17514', 'UNIPROID', [
            ['INHBA_HUMAN', 'INHBB_HUMAN', 'INHBC_HUMAN', 'INHBE_HUMAN']]]
    ])
    def test_parse_ttd_file_values(self, target_id, abbrev, value):
        parsed_result = self.ttd.parse_ttd_file(self.ttd_dl_snippet)
        self.assertCountEqual(parsed_result.get(target_id).get(abbrev), value,
                              "Problem in parse_ttd_file for {} {} {}".
                              format(target_id, abbrev, value))


    def test_run(self) -> None:
        self.assertTrue(isinstance(getattr(self.ttd, "run"), types.MethodType))
