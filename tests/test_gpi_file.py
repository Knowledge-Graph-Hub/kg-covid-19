import os
import unittest

from kg_covid_19.transform_utils.sars_cov_2_gene_annot.sars_cov_2_gene_annot import \
    _gpi12iterator


class TestGpiFile(unittest.TestCase):
    def setUp(self) -> None:
        self.gpi_file = 'curated/ORFs/uniprot_sars-cov-2.gpi'
        self.expected_sars_cov2_genes = 32

    def test_gpi_file_exists(self):
        self.assertTrue(os.path.exists(self.gpi_file))

    def test_gpi_parsing(self):
        count: int = 0
        with open(self.gpi_file, 'r') as gpi_fh:
            for rec in _gpi12iterator(gpi_fh):
                count += 1
        self.assertEqual(self.expected_sars_cov2_genes, count)
