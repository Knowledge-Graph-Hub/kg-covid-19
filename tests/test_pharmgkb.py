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
            self.rel_file_header = r.readline().strip().split('\t')
            self.rel_file_lines = r.readlines()

        self.pharmgkb_gene_map_snippet =\
            "tests/resources/pharmgkb_gene_SNIPPET.tsv"
        with open(self.pharmgkb_gene_map_snippet, 'r') as r:
            self.gene_file_header = r.readline().strip().split('\t')
            self.gene_file_lines = r.readlines()

    def test_parse_pharmgkb_line(self) -> None:
        self.assertTrue(isinstance(getattr(self.pharmgkb, "parse_pharmgkb_line"),
                                   types.MethodType))
        parsed_result = self.pharmgkb.parse_pharmgkb_line(self.rel_file_lines[0],
                                                          self.rel_file_header)
        self.assertTrue(isinstance(parsed_result, dict))
        self.assertCountEqual(parsed_result.keys(),
                              ['Entity1_id','Entity1_name','Entity1_type',
                               'Entity2_id','Entity2_name','Entity2_type',
                               'Evidence','Association','PK','PD'])
        self.assertTrue(parsed_result['Entity1_name'], 'ANKFN1')

    def test_make_id_mapping_file(self) -> None:
        self.assertTrue(isinstance(getattr(self.pharmgkb, "make_id_mapping_file"),
                                   types.MethodType))
        parsed_result = self.pharmgkb.make_id_mapping_file(
            self.pharmgkb_gene_map_snippet)
        self.assertTrue(isinstance(parsed_result, dict))
        self.assertCountEqual(parsed_result.keys(), ['PA24356', 'PA165392995'])
        self.assertTrue('parsed_ids' in parsed_result['PA24356'])
        self.assertTrue('UniProtKB' in parsed_result['PA24356']['parsed_ids'])
        self.assertTrue(parsed_result['PA24356']['parsed_ids']['UniProtKB'],
                        "P04217")

    def test_run(self) -> None:
        self.assertTrue(isinstance(getattr(self.pharmgkb, "run"), types.MethodType))
