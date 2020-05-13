from unittest import TestCase

import pandas as pd

from kg_covid_19.query_utils.target_candidates.target_candidates import TargetCandidates


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
            "tests/test_sars_cov2_pro_candidates_nodes_SNIPPET.tsv", sep="\t")

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

    def test_sars_cov2_and_intact_to_candidate_entries(self):
        self.assertTrue(hasattr(self.tc, 'sars_cov2_and_intact_to_candidate_entries'))
        edges_df = pd.read_csv("tests/resources/P0DTC1.edges.tsv", sep="\t")
        nodes_df = pd.read_csv("tests/resources/P0DTC1.nodes.tsv", sep="\t")

        candidates = self.tc.sars_cov2_and_intact_to_candidate_entries(
                            ['bar', 'baz'],
                            ['intact'],
                            edges_df,
                            nodes_df,
                            'H',
                            ['subject', 'object'],
                            'name',
                            0.5,
                            'interacts with SARS-CoV-2 protein according to IntAct')
        self.assertEqual(1, len(candidates))
        self.assertEqual(len(candidates[0]), 5)
        # self.assertEqual(
        #                  ['V',
        #                   'UniProtKB:O75347',
        #                   'tbca_human',
        #                   0.5,
        #                   'interacts with SARS-CoV-2 protein according to IntAct'],
        #                  candidates[0])
