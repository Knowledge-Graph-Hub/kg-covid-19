import os
import tempfile
from unittest import TestCase, skip

from parameterized import parameterized

from kg_covid_19.transform_utils.string_ppi import StringTransform


class TestString(TestCase):
    """Tests the string ingest"""
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_dir = "tests/resources/string/"
        cls.output_dir = tempfile.gettempdir()
        cls.string_output_dir = os.path.join(cls.output_dir, "STRING")
        cls.string = StringTransform(cls.input_dir, cls.output_dir)

    def setUp(self) -> None:
        pass

    @parameterized.expand([
    ['ensembl2ncbi_map', dict, 'ENSG00000121410', 1],
    ['gene_info_map', dict, '1',
     {'ENSEMBL': 'ENSG00000121410', 'symbol': 'A1BG',
      'description': 'alpha-1-B glycoprotein'}],
    ['protein_gene_map', dict, 'ENSP00000263100', 'ENSG00000121410'],
    ])
    def test_instance_vars(self, variable, type, key, val):
        this_var = getattr(self.string, variable)
        self.assertTrue(isinstance(this_var, type))
        self.assertTrue(key in this_var)
        self.assertTrue(this_var[key], val)

    def test_output_dir(self):
        self.assertEqual(self.string.output_dir, self.string_output_dir)

    def test_input_dir(self):
        self.assertEqual(self.string.input_base_dir, self.input_dir)

    def test_output_edge_file(self):
        self.assertEqual(self.string.output_edge_file,
                         os.path.join(self.string_output_dir, "edges.tsv"))

    def test_output_node_file(self):
        self.assertEqual(self.string.output_node_file,
                         os.path.join(self.string_output_dir, "nodes.tsv"))

    def test_source_name(self):
        self.assertEqual(self.string.source_name, 'STRING')

    def test_run(self):
        self.assertTrue(isinstance(self.string.run, object))
        self.string.run()
        self.assertTrue(os.path.isdir(self.string_output_dir))
        self.assertTrue(
            os.path.isfile(os.path.join(self.string_output_dir, "nodes.tsv")))
        self.assertTrue(
            os.path.isfile(os.path.join(self.string_output_dir, "edges.tsv")))
