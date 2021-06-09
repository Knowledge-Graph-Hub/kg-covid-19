import io
import os
import sys
import tempfile
import unittest
from kg_covid_19.transform_utils.gocam_transform import GocamTransform


class TestGOCams(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.gc_nt_file = 'tests/resources/gocams/lifted-go-cams-20200619_SNIPPET.nt'
        cls.input_dir = 'tests/resources/gocams/'
        cls.output_dir = tempfile.gettempdir()
        cls.gocams_t = GocamTransform(input_dir=cls.input_dir,
                                      output_dir=cls.output_dir)

        # Suppress chatter
        # suppress_text = io.StringIO()
        # sys.stdout = suppress_text
        cls.gocams_t.run(data_file=cls.gc_nt_file)
        # sys.stdout = sys.__stdout__

    def setUp(self) -> None:
        self.dc_output_dir = os.path.join(self.output_dir, "gocams")
        self.expected_nodes_file = os.path.join(self.dc_output_dir, 'GOCAMs_nodes.tsv')
        self.expected_edges_file = os.path.join(self.dc_output_dir, 'GOCAMs_edges.tsv')
        self.expected_num_nodes = 3682
        self.expected_num_edges = 4161

    def test_run(self):
        self.assertTrue(isinstance(self.gocams_t.run, object))
        self.assertTrue(os.path.isdir(self.dc_output_dir))

    def test_nodes_file_exists(self):
        self.assertTrue(os.path.isfile(self.expected_nodes_file))

    def test_num_transformed_nodes(self):
        self.assertTrue(sum(1 for line in open(self.expected_nodes_file)) > 1)

    def test_edges_file_exists(self):
        self.assertTrue(os.path.isfile(self.expected_edges_file))

    def test_num_transformed_edges(self):
        self.assertTrue(sum(1 for line in open(self.expected_edges_file)) > 1)

