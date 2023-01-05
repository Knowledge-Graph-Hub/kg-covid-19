"""Tests for the SARS-CoV-2 gene annotation parsing."""

from typing import Iterable
from unittest import TestCase

from parameterized import parameterized

from kg_covid_19.transform_utils.sars_cov_2_gene_annot import SARSCoV2GeneAnnot
from kg_covid_19.transform_utils.sars_cov_2_gene_annot.sars_cov_2_gene_annot import (
    _gpa11iterator, _gpi12iterator)


class TestSarsGeneAnnot(TestCase):
    """Tests for the SARS-CoV-2 gene annotation transform."""

    def setUp(self) -> None:
        """Set up for the tests."""
        self.sc2ga = SARSCoV2GeneAnnot()
        self.gpi_snippet = "tests/resources/uniprot_sars-cov-2_SNIPPET.gpi"
        self.gpa_snippet = "tests/resources/uniprot_sars-cov-2_SNIPPET.gpa"
        self.gpi_fh = open(self.gpi_snippet)
        self.gpa_fh = open(self.gpa_snippet)

    def test_gpi12iterator_instance(self):
        """Test that the gpi parser provides an iterator instance."""
        gpi_iter = _gpi12iterator(self.gpi_fh)
        self.assertTrue(isinstance(gpi_iter, Iterable))

    @parameterized.expand(
        [
            ("DB", "UniProtKB"),
            ("DB_Object_ID", "P0DTD2"),
            ("DB_Object_Symbol", ["P0DTD2"]),
            ("DB_Object_Name", ["Protein 9b"]),
            ("DB_Object_Synonym", ""),
            ("DB_Object_Type", "protein"),
            ("DB_Xref", ["PR:000050272", "UniProtKB:P0DTD1-PRO_0000449637"]),
            ("Taxon", "taxon:2697049"),
        ]
    )
    def test_gpi12iterator_keys(self, key, value):
        """Test that the gpi iterator is not empty."""
        gpi_iter = _gpi12iterator(self.gpi_fh)
        item = next(gpi_iter)
        self.assertTrue(key in item)
        self.assertEqual(value, item[key])

    def test_gpi_to_gene_node(self):
        """Test that the gpi iterator parses names to nodes."""
        gpi_iter = _gpi12iterator(self.gpi_fh)
        item = next(gpi_iter)
        node = self.sc2ga.gpi_to_gene_node_data(item)
        self.assertEqual(len(self.sc2ga.node_header), len(node))
        self.assertEqual(
            node,
            [
                "UniProtKB:P0DTD2",
                "P0DTD2",
                "biolink:Protein",
                "Protein 9b",
                "",
                "NCBITaxon:2697049",
                "PR:000050272|UniProtKB:P0DTD1-PRO_0000449637",
                "sars_cov_2_gene_annot",
            ],
        )

    def test_gpa_to_edge_data(self):
        """Test that the gpi iterator parses edges."""
        gpa_iter = _gpa11iterator(self.gpa_fh)
        edge1 = self.sc2ga.gpa_to_edge_data(next(gpa_iter))
        edge2 = self.sc2ga.gpa_to_edge_data(next(gpa_iter))

        self.assertEqual(len(self.sc2ga.edge_header), len(edge1))
        self.assertEqual(
            edge1,
            [
                "UniProtKB:P0DTC1",
                "biolink:enables",
                "GO:0003723",
                "RO:0002327",
                "sars_cov_2_gene_annot",
                "biolink:Association",
                "GO_REF:0000043",
                "ECO:0000322",
                "UniProtKB-KW:KW-0694",
                "",
                "20200321",
                "UniProt",
                "",
                "go_evidence=IEA",
            ],
        )

        # # check another RO term too
        self.assertEqual(edge2[1], "biolink:involved_in")
        self.assertEqual(edge2[3], "RO:0002331")

    def test_run(self) -> None:
        """Test the existence of the full gene annotation method."""
        self.assertTrue(hasattr(self.sc2ga, "run"))
