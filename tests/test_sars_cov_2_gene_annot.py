import types
from typing import Iterable
from unittest import TestCase

from Bio.UniProt.GOA import gpa_iterator
from parameterized import parameterized

from kg_covid_19.transform_utils.sars_cov_2_gene_annot import SARSCoV2GeneAnnot
from kg_covid_19.transform_utils.sars_cov_2_gene_annot.sars_cov_2_gene_annot import \
    _gpi12iterator


class TestPharmGKB(TestCase):
    """Tests the ttd transform"""

    def setUp(self) -> None:
        self.sc2ga = SARSCoV2GeneAnnot()
        self.gpi_snippet = "tests/resources/uniprot_sars-cov-2_SNIPPET.gpi"
        self.gpa_snippet = "tests/resources/uniprot_sars-cov-2_SNIPPET.gpa"
        self.gpi_fh = open(self.gpi_snippet)
        self.gpa_fh = open(self.gpa_snippet)

    def test_gpi12iterator_instance(self):
        gpi_iter = _gpi12iterator(self.gpi_fh)
        self.assertTrue(isinstance(gpi_iter, Iterable))

    @parameterized.expand([
        ('DB', 'UniProtKB'),
        ('DB_Object_ID', 'P0DTD2'),
        ('DB_Object_Symbol', ['P0DTD2']),
        ('DB_Object_Name', ['Protein 9b']),
        ('DB_Object_Synonym', ''),
        ('DB_Object_Type', 'protein'),
        ('Taxon', 'taxon:2697049'),
    ])
    def test_gpi12iterator_instance(self, key, value):
        gpi_iter = _gpi12iterator(self.gpi_fh)
        item = next(gpi_iter)
        self.assertTrue(key in item)
        self.assertEqual(item[key], value)

    def test_gpi_to_gene_node(self):
        gpi_iter = _gpi12iterator(self.gpi_fh)
        item = next(gpi_iter)
        node = self.sc2ga.gpi_to_gene_node(item)
        self.assertEqual(len(self.sc2ga.node_header), len(node))
        self.assertEqual(node,
                         ['UniProtKB:P0DTD2', 'Protein 9b', 'biolink:Protein', '', 'taxon:2697049'])

    def test_gpa_to_gene_node(self):
        gpa_iter = gpa_iterator(self.gpa_fh)
        item = next(gpa_iter)
        edge = self.sc2ga.gpa_to_gene_node(item)
        # self.assertEqual(len(self.sc2ga.edge_header), len(edge))
        # UniProtKB	P0DTC1	enables	GO:0003723	GO_REF:0000043	ECO:0000322	UniProtKB-KW:KW-0694		20200321	UniProt		go_evidence=IEA
        # ['subject', 'edge_label', 'object', 'relation']
        # self.assertEqual(edge,
        #                  ['UniProtKB:P0DTD2', 'enables', 'biolink:Protein', '', 'taxon:2697049'])

    def test_run(self) -> None:
        self.assertTrue(isinstance(getattr(self.sc2ga, "run"), types.MethodType))
