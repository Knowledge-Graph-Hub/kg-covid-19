import unittest
from parameterized import parameterized
from kg_covid_19.utils.transform_utils import guess_bl_category, collapse_uniprot_curie


class TestTransformUtils(unittest.TestCase):
    @parameterized.expand([
        ['', 'biolink:NamedThing'],
        ['UniProtKB', 'biolink:Protein'],
        ['ComplexPortal', 'biolink:Protein'],
        ['GO', 'biolink:OntologyClass'],
    ])
    def test_guess_bl_category(self, curie, category):
        self.assertEqual(category, guess_bl_category(curie))

    @parameterized.expand([
        ['foobar', 'foobar'],
        ['ENSEMBL:ENSG00000178607', 'ENSEMBL:ENSG00000178607'],
        ['UniprotKB:P63151-1', 'UniprotKB:P63151'],
        ['uniprotkb:P63151-1', 'uniprotkb:P63151'],
        ['UniprotKB:P63151-2', 'UniprotKB:P63151'],
    ])
    def test_collapse_uniprot_curie(self, curie, collapsed_curie):
        self.assertEqual(collapsed_curie, collapse_uniprot_curie(curie))

