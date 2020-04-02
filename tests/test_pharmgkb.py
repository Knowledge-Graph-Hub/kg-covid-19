import types
from unittest import TestCase

from kg_covid_19.transform_utils.pharmgkb import PharmGKB


class TestPharmGKB(TestCase):
    """Tests the ttd transform"""

    def setUp(self) -> None:
        self.pharmgkb = PharmGKB()
        self.pharmgkb_relationships_snippet =\
            "tests/resources/relationships_SNIPPET.tsv"
        with open(self.pharmgkb_relationships_snippet, 'r') as r:
            self.file_header = r.readline().strip().split('\t')
            self.file_lines = r.readlines()

    def test_parse_pharmgkb_line(self) -> None:
        self.assertTrue(isinstance(getattr(self.pharmgkb, "parse_pharmgkb_line"),
                                   types.MethodType))
        parsed_result = self.pharmgkb.parse_pharmgkb_line(self.file_lines[0],
                                                          self.file_header)
        self.assertTrue(isinstance(parsed_result, dict))
        self.assertCountEqual(parsed_result.keys(),
                              ['Entity1_id','Entity1_name','Entity1_type',
                               'Entity2_id','Entity2_name','Entity2_type',
                               'Evidence','Association','PK','PD'])
        self.assertTrue(parsed_result['Entity1_name'], 'ANKFN1')

    def test_run(self) -> None:
        self.assertTrue(isinstance(getattr(self.pharmgkb, "run"), types.MethodType))
