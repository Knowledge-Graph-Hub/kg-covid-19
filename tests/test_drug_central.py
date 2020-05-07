import unittest

from kg_covid_19.transform_utils.drug_central.drug_central import \
    parse_drug_central_line
from kg_covid_19.utils.transform_utils import parse_header
from parameterized import parameterized


class TestDrugCentral(unittest.TestCase):

    def setUp(self) -> None:
        self.dti_fh = open('tests/resources/drug.target.interaction_SNIPPET.tsv', 'rt')

    @parameterized.expand([
     ('STRUCT_ID', '4'),
     ('TARGET_NAME', 'Sodium channel protein type 4 subunit alpha'),
     ('TARGET_CLASS', 'Ion channel'),
     ('ACCESSION', 'P35499'),
     ('GENE', 'SCN4A'),
     ('SWISSPROT', 'SCN4A_HUMAN'),
     ('ACT_VALUE', ''),
     ('ACT_UNIT', ''),
     ('ACT_TYPE', ''),
     ('ACT_COMMENT', ''),
     ('ACT_SOURCE', 'WOMBAT-PK'),
     ('RELATION', ''),
     ('MOA', '1'),
     ('MOA_SOURCE', 'CHEMBL'),
     ('ACT_SOURCE_URL', ''),
     ('MOA_SOURCE_URL', 'https://www.ebi.ac.uk/chembl/compound/inspect/CHEMBL1200749'),
     ('ACTION_TYPE', 'BLOCKER'),
     ('TDL', 'Tclin'),
     ('ORGANISM', 'Homo sapiens')])
    def test_parse_drug_central_line(self, key, value):
        header = parse_header(self.dti_fh.readline())
        line = self.dti_fh.readline()
        parsed = parse_drug_central_line(line, header)
        self.assertTrue(key in parsed)
        self.assertEqual(value, parsed[key])


