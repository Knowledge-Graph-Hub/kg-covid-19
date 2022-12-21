"""Test for parsing DrugCentral data."""

import os
import tempfile
import unittest

import pandas as pd
from parameterized import parameterized

from kg_covid_19.transform_utils.drug_central import DrugCentralTransform
from kg_covid_19.transform_utils.drug_central.drug_central import \
    parse_drug_central_line
from kg_covid_19.utils.transform_utils import parse_header


class TestDrugCentral(unittest.TestCase):
    """Tests for DrugCentral data."""

    def setUp(self) -> None:
        """Set up the tests."""
        self.dti_fh = open(
            "tests/resources/drug_central/drug.target.interaction_SNIPPET.tsv", "rt"
        )
        self.input_dir = "tests/resources/drug_central/"
        self.output_dir = tempfile.gettempdir()
        self.dc_output_dir = os.path.join(self.output_dir, "drug_central")
        self.drug_central = DrugCentralTransform(
            input_dir=self.input_dir, output_dir=self.output_dir
        )

    @parameterized.expand(
        [
            ("STRUCT_ID", "4"),
            ("TARGET_NAME", "Sodium channel protein type 4 subunit alpha"),
            ("TARGET_CLASS", "Ion channel"),
            ("ACCESSION", "P35499"),
            ("GENE", "SCN4A"),
            ("SWISSPROT", "SCN4A_HUMAN"),
            ("ACT_VALUE", ""),
            ("ACT_UNIT", ""),
            ("ACT_TYPE", ""),
            ("ACT_COMMENT", ""),
            ("ACT_SOURCE", "WOMBAT-PK"),
            ("RELATION", ""),
            ("MOA", "1"),
            ("MOA_SOURCE", "CHEMBL"),
            ("ACT_SOURCE_URL", ""),
            (
                "MOA_SOURCE_URL",
                "https://www.ebi.ac.uk/chembl/compound/inspect/CHEMBL1200749",
            ),
            ("ACTION_TYPE", "BLOCKER"),
            ("TDL", "Tclin"),
            ("ORGANISM", "Homo sapiens"),
        ]
    )
    def test_parse_drug_central_line(self, key, value):
        """Test parsing of DrugCentral data, by lines."""
        header = parse_header(self.dti_fh.readline())
        line = self.dti_fh.readline()
        parsed = parse_drug_central_line(line, header)
        self.assertTrue(key in parsed)
        self.assertEqual(value, parsed[key])

    def test_run(self):
        """Test the full DrugCentral transformation."""
        self.assertTrue(isinstance(self.drug_central.run, object))
        self.drug_central.run(data_file="drug.target.interaction_SNIPPET.tsv.gz")
        self.assertTrue(os.path.isdir(self.dc_output_dir))

    def test_nodes_file(self):
        """Test the integrity of the nodes file."""
        self.drug_central.run(data_file="drug.target.interaction_SNIPPET.tsv.gz")
        node_file = os.path.join(self.dc_output_dir, "nodes.tsv")
        self.assertTrue(os.path.isfile(node_file))
        node_df = pd.read_csv(node_file, sep="\t", header=0)
        self.assertEqual((23, 5), node_df.shape)
        self.assertEqual(
            ["id", "name", "category", "TDL", "provided_by"], list(node_df.columns)
        )
        self.assertListEqual(
            [
                "DrugCentral:4",
                "UniProtKB:P35499",
                "UniProtKB:P10635",
                "UniProtKB:Q12809",
                "UniProtKB:Q9UK17",
                "UniProtKB:P34995",
                "UniProtKB:P35498",
                "UniProtKB:P22460",
                "UniProtKB:P46098",
                "DrugCentral:5",
                "UniProtKB:Q01668",
                "UniProtKB:Q13936",
                "DrugCentral:6",
                "UniProtKB:O15554",
                "UniProtKB:O60840",
                "DrugCentral:38",
                "UniProtKB:O15399",
                "UniProtKB:O60391",
                "UniProtKB:Q05586",
                "UniProtKB:Q12879",
                "UniProtKB:Q13224",
                "UniProtKB:Q14957",
                "UniProtKB:Q8TCU5",
            ],
            list(node_df.id.unique()),
        )

    def test_nodes_are_not_repeated(self):
        """Test that nodes are not repeated in the output."""
        self.drug_central.run(data_file="drug.target.interaction_SNIPPET.tsv.gz")
        node_file = os.path.join(self.dc_output_dir, "nodes.tsv")
        node_df = pd.read_csv(node_file, sep="\t", header=0)
        nodes = list(node_df.id)
        unique_nodes = list(set(nodes))
        self.assertCountEqual(nodes, unique_nodes)

    def test_edges_file(self):
        """Test integrity of the edges file."""
        self.drug_central.run(data_file="drug.target.interaction_SNIPPET.tsv.gz")
        edge_file = os.path.join(self.dc_output_dir, "edges.tsv")
        self.assertTrue(os.path.isfile(edge_file))
        edge_df = pd.read_csv(edge_file, sep="\t", header=0)
        self.assertEqual((21, 7), edge_df.shape)
        self.assertEqual(
            [
                "subject",
                "predicate",
                "object",
                "relation",
                "provided_by",
                "comment",
                "type",
            ],
            list(edge_df.columns),
        )
