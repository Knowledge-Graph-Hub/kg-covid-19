"""Test the parent Transform class."""

import os
from unittest import TestCase

from parameterized import parameterized

from kg_covid_19.transform import DATA_SOURCES
from kg_covid_19.transform_utils.transform import Transform


class TestTransform(TestCase):
    """Tests for all transform child classes."""

    def setUp(self) -> None:
        """Set up the transform tests."""
        self.transform_instance = TransformChildClass()

    def test_reality(self):
        """Test the nature of reality."""
        self.assertEqual(1, 1)

    @parameterized.expand(
        [
            ("source_name", "test_transform"),
            ("node_header", ["id", "name", "category"]),
            (
                "edge_header",
                ["subject", "predicate", "object", "relation", "provided_by"],
            ),
            ("output_base_dir", os.path.join("data", "transformed")),
            ("input_base_dir", os.path.join("data", "raw")),
            ("output_dir", os.path.join("data", "transformed", "test_transform")),
            (
                "output_node_file",
                os.path.join("data", "transformed", "test_transform", "nodes.tsv"),
            ),
            (
                "output_edge_file",
                os.path.join("data", "transformed", "test_transform", "edges.tsv"),
            ),
            (
                "output_json_file",
                os.path.join(
                    "data", "transformed", "test_transform", "nodes_edges.json"
                ),
            ),
        ]
    )
    def test_attributes(self, attr, default):
        """Test the attributes of a Transform instance."""
        self.transform_instance
        self.assertTrue(hasattr(self.transform_instance, attr))
        self.assertEqual(getattr(self.transform_instance, attr), default)

    @parameterized.expand(
        [("DEFAULT_INPUT_DIR", "data/raw"), ("DEFAULT_OUTPUT_DIR", "data/transformed")]
    )
    def test_default_dir(self, dir_var_name, dir_var_value):
        """Test the default directory."""
        self.assertEqual(getattr(Transform, dir_var_name), dir_var_value)

    @parameterized.expand(
        list(DATA_SOURCES.keys()),
    )
    def test_transform_child_classes(self, src_name):
        """
        Test whether Transform child classes work as expected.

        Make sure Transform child classes:
        - properly set default input_dir and output_dir
        - properly pass and set input_dir and output from constructor
        - implement run()
        :param src_name:
        :return: None
        """
        input_dir = os.path.join("tests", "resources")
        output_dir = os.path.join("output")
        def_input_dir = os.path.join("data", "raw")
        def_output_dir = os.path.join("data", "transformed")

        t = DATA_SOURCES[src_name](input_dir=input_dir, output_dir=output_dir)
        self.assertEqual(t.input_base_dir, input_dir)
        self.assertEqual(t.output_base_dir, output_dir)
        self.assertTrue(hasattr(t, "run"))
        self.assertEqual(t.DEFAULT_INPUT_DIR, def_input_dir)
        self.assertEqual(t.DEFAULT_OUTPUT_DIR, def_output_dir)


class TransformChildClass(Transform):
    """An example Transform class."""

    def __init__(self):
        """Initialize a Transform child class."""
        super().__init__(source_name="test_transform")
