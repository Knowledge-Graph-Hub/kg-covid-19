import os
import tempfile
import unittest

from kg_covid_19.transform_utils.drug_central.drug_central import \
    parse_drug_central_line, unzip_and_get_tclin_tchem, tsv_to_dict
from kg_covid_19.utils.transform_utils import parse_header
from parameterized import parameterized


class TestDrugCentral(unittest.TestCase):

    def setUp(self) -> None:
        self.dti_fh = open(
            'tests/resources/drug_central/drug.target.interaction_SNIPPET.tsv', 'rt')

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

    @parameterized.expand([
    ('tclin', 'tests/resources/drug_central/tclin_SNIPPET.tsv', 2, 'Q13131', 'drug_name', 'cepharanthine'),
    ('tchem', 'tests/resources/drug_central/tchem_SNIPPET.tsv', 2, 'P21917', 'drug_name', 'brexpiprazole'),
    ])
    def test_tsv_to_dict(self, name, file, expected_rows, test_key, sub_key, test_val) -> None:
        ret_val = tsv_to_dict(file, 'uniprot')
        self.assertTrue(isinstance(ret_val, dict))
        self.assertEqual(len(ret_val), expected_rows)
        self.assertTrue(isinstance(ret_val, dict))
        self.assertTrue(test_key in ret_val)
        self.assertTrue(sub_key in ret_val.get(test_key))
        self.assertEqual(ret_val[test_key][sub_key], test_val)


    def test_unzip_and_get_tclin_tchem(self) -> None:
        zip_file = "tests/resources/drug_central/test.zip"
        tempdir = tempfile.mkdtemp()
        (tclin, tchem) = unzip_and_get_tclin_tchem(zip_file, tempdir)
        self.assertTrue(isinstance(tclin, str))
        self.assertTrue(isinstance(tchem, str))
        self.assertEqual(tclin, os.path.join(tempdir, 'tclin_05122020.tsv'))
        self.assertEqual(tchem, os.path.join(tempdir, 'tchem_drugs_05122020.tsv'))

