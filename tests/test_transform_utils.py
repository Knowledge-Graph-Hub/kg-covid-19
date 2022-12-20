"""Test the transformation utilities."""

import unittest

from parameterized import parameterized

from kg_covid_19.utils.transform_utils import (collapse_uniprot_curie,
                                               guess_bl_category)


class TestTransformUtils(unittest.TestCase):
    @parameterized.expand(
        [
            ["", "biolink:NamedThing"],
            ["UniProtKB", "biolink:Protein"],
            ["ComplexPortal", "biolink:Protein"],
            ["GO", "biolink:OntologyClass"],
        ]
    )
    def test_guess_bl_category(self, curie, category):
        """Test inference of Biolink categories for a CURIE."""
        self.assertEqual(category, guess_bl_category(curie))

    @parameterized.expand(
        [
            ["foobar", "foobar"],
            ["ENSEMBL:ENSG00000178607", "ENSEMBL:ENSG00000178607"],
            ["UniprotKB:P63151-1", "UniprotKB:P63151"],
            ["uniprotkb:P63151-1", "uniprotkb:P63151"],
            ["UniprotKB:P63151-2", "UniprotKB:P63151"],
        ]
    )
    def test_collapse_uniprot_curie(self, curie, collapsed_curie):
        """Test for collapsing a UniProtKB curie."""
        self.assertEqual(collapsed_curie, collapse_uniprot_curie(curie))
