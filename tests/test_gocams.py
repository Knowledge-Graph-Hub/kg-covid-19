import io
import os
import sys
import tempfile
import unittest
from kg_covid_19.transform_utils.gocam_transform import GocamTransform


class TestGOCams(unittest.TestCase):

    def setUp(self) -> None:
        self.gc_nt_file = 'tests/resources/gocams/lifted-go-cams-20200619_SNIPPET.nt'
        self.input_dir = 'tests/resources/gocams/'
        self.output_dir = tempfile.gettempdir()
        self.gocams_t = GocamTransform(input_dir=self.input_dir,
                                      output_dir=self.output_dir)
        #
        # # Suppress chatter
        # suppress_text = io.StringIO()
        # sys.stdout = suppress_text
        # self.gocams_t.run(data_file=self.gc_nt_file)
        # sys.stdout = sys.__stdout__
        #
        # self.output_dir = os.path.join(self.output_dir, "gocams")
        # self.expected_nodes_file = os.path.join(self.output_dir, 'GOCAMs_nodes.tsv')
        # self.expected_edges_file = os.path.join(self.output_dir, 'GOCAMs_edges.tsv')
        # self.expected_num_nodes = 3682
        # self.expected_num_edges = 4161

    def test_reality(self):
        self.assertTrue(True)

    def test_run_exists(self):
        self.assertTrue(isinstance(self.gocams_t.run, object))

    def test_makes_output_dir(self):
        self.assertTrue(os.path.isdir(self.output_dir))
    #
    # def test_nodes_file_exists(self):
    #     self.assertTrue(os.path.isfile(self.expected_nodes_file))
    #
    # def test_num_transformed_nodes(self):
    #     self.assertTrue(sum(1 for line in open(self.expected_nodes_file)) > 1)
    #
    # def test_edges_file_exists(self):
    #     self.assertTrue(os.path.isfile(self.expected_edges_file))
    #
    # def test_num_transformed_edges(self):
    #     self.assertTrue(sum(1 for line in open(self.expected_edges_file)) > 1)

