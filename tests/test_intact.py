import unittest

from kg_covid_19.transform_utils.intact.intact import IntAct


class TestIntAct(unittest.TestCase):

    def setUp(self) -> None:
        self.xml_file = 'tests/resources/intact_test.xml'
        self.intact = IntAct()

    def test_struct_parse_xml_to_nodes_edges(self):
        parsed = self.intact.parse_xml_to_nodes_edges(self.xml_file)
        self.assertTrue(isinstance(parsed, dict))
        self.assertTrue(isinstance(parsed['nodes'], list))
        self.assertTrue(isinstance(parsed['edges'], list))

    def test_nodes_parse_xml_to_nodes_edges(self):
        parsed = self.intact.parse_xml_to_nodes_edges(self.xml_file)
        self.assertEqual(len(parsed['nodes']), 5,
                         "Didn't get the expected number of nodes")
        self.assertCountEqual(parsed['nodes'][0],
                              ['uniprotkb:P20290', 'btf3_human', 'biolink:Protein'])
        # one xml contains an RNA interaction, so let's test that
        # we parse that correctly
        self.assertCountEqual(parsed['nodes'][1],
                              ['uniprotkb:P0C6X7-PRO_0000037317', 'nsp10_cvhsa',
                               'biolink:RNA'])

    @unittest.skip
    def test_edges_parse_xml_to_nodes_edges(self):
        parsed = self.intact.parse_xml_to_nodes_edges(self.xml_file)
        self.assertTrue(False)

