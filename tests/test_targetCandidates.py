from unittest import TestCase

import pandas as pd

from kg_covid_19.query_utils.target_candidates.target_candidates import TargetCandidates


class TestTargetCandidates(TestCase):
    def setUp(self) -> None:
        self.tc = TargetCandidates("/dev/null", "/dev/null")

    def test_sars_cov2_to_candidate_entry(self):
        self.assertTrue(hasattr(self.tc, 'sars_cov2_to_candidate_entry'))
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
        self.assertEqual(
                         ["V",
                          "UniProtKB:P0DTD2",
                          "Protein 9b",
                          1,
                          "annotated SARS-CoV-2 gene"],
                         candidates[0])
