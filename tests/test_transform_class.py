import os
from unittest import TestCase

from parameterized import parameterized
from kg_covid_19.transform_utils.transform import Transform


class TestTransform(TestCase):

    def setUp(self) -> None:
        self.transform_instance = TransformChildClass()

    def test_reality(self):
        self.assertEqual(1,1)

    @parameterized.expand([
        ('source_name', 'test_transform'),
        ('node_header', ['id', 'name', 'category']),
        ('edge_header',
         ['subject', 'edge_label', 'object', 'relation', 'provided_by']),
        ('output_base_dir', os.path.join("data", "transformed")),
        ('input_base_dir', os.path.join("data", "raw")),
        ('output_dir', os.path.join("data", "transformed", "test_transform")),
        ('output_node_file', os.path.join("data", "transformed", "test_transform", "nodes.tsv")),
        ('output_edge_file', os.path.join("data", "transformed", "test_transform", "edges.tsv")),
        ('output_json_file', os.path.join("data", "transformed", "test_transform", "nodes_edges.json"))
    ])
    def test_attributes(self, attr, default):
        self.transform_instance
        self.assertTrue(hasattr(self.transform_instance, attr))
        self.assertEqual(getattr(self.transform_instance, attr), default)


class TransformChildClass(Transform):
    def __init__(self):
        super().__init__(source_name="test_transform")
