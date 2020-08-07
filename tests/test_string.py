import os
import tempfile
import pandas as pd
from unittest import TestCase, skip

from parameterized import parameterized

from kg_covid_19.transform_utils.string_ppi import StringTransform


class TestString(TestCase):
    """Tests the string ingest"""
    def setUp(self) -> None:
        self.input_dir = "tests/resources/string/"
        self.output_dir = tempfile.gettempdir()
        self.string_output_dir = os.path.join(self.output_dir, "STRING")
        self.string = StringTransform(self.input_dir, self.output_dir)

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

    def test_nodes_file(self):
        self.string.run()
        node_file = os.path.join(self.string_output_dir, "nodes.tsv")
        self.assertTrue(os.path.isfile(node_file))
        node_df = pd.read_csv(node_file, sep="\t", header=0)
        self.assertEqual((10, 6), node_df.shape)
        self.assertEqual(['id', 'name', 'category', 'description', 'xrefs',
                          'provided_by'], list(node_df.columns))
        self.assertCountEqual(['ENSEMBL:ENSP00000000233',
                              'ENSEMBL:ENSP00000272298', 'ENSEMBL:ENSP00000253401',
                              'ENSEMBL:ENSP00000401445', 'ENSEMBL:ENSP00000418915',
                              'ENSEMBL:ENSP00000327801', 'ENSEMBL:ENSP00000466298',
                              'ENSEMBL:ENSP00000232564', 'ENSEMBL:ENSP00000393379',
                              'ENSEMBL:ENSP00000371253'],
                             list(node_df.id.unique()))
        self.assertEqual('UniProtKB:P84085',  # isoform (-2) stripped off
                              node_df.loc[node_df['id'] ==
                                          'ENSEMBL:ENSP00000000233'].xrefs.item())

    def test_edges_file(self):
        self.string.run()
        edge_file = os.path.join(self.string_output_dir, "edges.tsv")
        self.assertTrue(os.path.isfile(edge_file))
        edge_df = pd.read_csv(edge_file, sep="\t", header=0)
        self.assertEqual((9, 20), edge_df.shape)
        self.assertEqual(['subject', 'edge_label', 'object', 'relation', 'provided_by', 'type',
                          'combined_score', 'neighborhood', 'neighborhood_transferred',
                          'fusion', 'cooccurence', 'homology', 'coexpression',
                          'coexpression_transferred', 'experiments',
                          'experiments_transferred', 'database', 'database_transferred',
                          'textmining', 'textmining_transferred', ],
                         list(edge_df.columns))
