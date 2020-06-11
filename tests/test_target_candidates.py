from unittest import TestCase

import pandas as pd


class TestTargetCandidates(TestCase):
    def setUp(self) -> None:
        self.tc = TargetCandidates("/dev/null", "/dev/null")

    def test_sars_cov2_to_candidate_entry(self):
        self.assertTrue(hasattr(self.tc, 'sars_cov2_to_candidate_entries'))
        sars_cov2_df = pd.read_csv("tests/resources/sars_cov_2_gene_annot_SNIPPET.tsv",
                                   sep="\t")
        candidates = self.tc.sars_cov2_to_candidate_entries(sars_cov2_df,
                                                          'V',
                                                          'id',
                                                          'name',
                                                            1,
                                                          "annotated SARS-CoV-2 gene"
                                                            )
        self.assertEqual(len(candidates), 2)
        self.assertEqual(len(candidates[0]), 5)
        self.assertEqual(
                         ["V",
                          "UniProtKB:P0DTD2",
                          "Protein 9b",
                          1,
                          "annotated SARS-CoV-2 gene"],
                         candidates[0])

    def test_sars_cov2_pro_candidates(self):
        sars_cov_df = pd.read_csv(
            "tests/resources/test_sars_cov2_pro_candidates_nodes_SNIPPET.tsv", sep="\t")

        candidates = self.tc.sars_cov2_pro_candidates(
                                                        ["UniProtKB:P0DTC1"],
                                                        sars_cov_df,
                                                        'V', 'id', 'name', 1,
                                                        "annotated SARS-CoV-2 gene")
        self.assertEqual(1, len(candidates))
        self.assertEqual(len(candidates[0]), 5)
        self.assertEqual(
                         ["V",
                          "UniProtKB:P0DTC1-PRO_0000449645",
                          "p0dtc1-pro_0000449645",
                          1,
                          "annotated SARS-CoV-2 gene"],
                         candidates[0])

    def test_sars_cov2_in_intact_set_to_candidate_entries(self):
        self.assertTrue(hasattr(self.tc,
                                'sars_cov2_in_intact_set_to_candidate_entries'))
        existing_ids = ['UniProtKB:P0DTC2']  # don't want these again
        nodes_df = pd.read_csv("tests/resources/test_sars_cov2_intact_nodes.tsv",
                               sep="\t")
        candidates = self.tc.sars_cov2_in_intact_set_to_candidate_entries(
                        existing_ids=existing_ids,
                        taxon_id=2697049,
                        nodes_df=nodes_df,
                        taxid_col='ncbi_taxid')
        self.assertEqual(1, len(candidates))
        self.assertEqual(
                         ['V',
                          'UniProtKB:P0DTD1-PRO_0000449619',
                          'nsp1_wcpv',
                          1,
                          'present in intact database'],
                         candidates[0])

    def test_sars_cov2_and_intact_to_candidate_entries(self):
        self.assertTrue(hasattr(self.tc,
                                'sars_cov2_human_interactors_to_candidate_entries'))
        edges_df = pd.read_csv("tests/resources/P0DTC1.edges.tsv", sep="\t")
        nodes_df = pd.read_csv("tests/resources/P0DTC1.nodes.tsv", sep="\t")

        candidates = self.tc.sars_cov2_human_interactors_to_candidate_entries(
                            ['UniProtKB:P0DTC1-PRO_0000449645', 'IDNOTINFILE'],
                            'intact',
                            edges_df,
                            nodes_df,
                            'H',
                            ['subject', 'object'],
                            'id',
                            'name',
                            0.5,
                            'interacts with SARS-CoV-2 protein according to IntAct')
        self.assertEqual(1, len(candidates))
        self.assertEqual(len(candidates[0]), 5)
        self.assertEqual(
                         ['H',
                          'UniProtKB:O75347',
                          'tbca_human',
                          0.5,
                          'interacts with SARS-CoV-2 protein according to IntAct'],
                         candidates[0])
