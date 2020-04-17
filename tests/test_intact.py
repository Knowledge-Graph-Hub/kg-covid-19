import unittest

from kg_covid_19.transform_utils.intact.intact import IntAct


class TestIntAct(unittest.TestCase):

    def setUp(self) -> None:
        self.xml_file = 'tests/resources/intact_test_16157265.xml'
        self.intact = IntAct()

    def test_struct_parse_xml_to_nodes_edges(self):
        (nodes, edges) = self.intact.parse_xml_to_nodes_edges(self.xml_file)
        self.assertTrue(isinstance(nodes, list))
        self.assertTrue(isinstance(edges, list))

    def test_nodes_parse_xml_to_nodes_edges(self):
        (nodes, _) = self.intact.parse_xml_to_nodes_edges(self.xml_file)
        self.assertTrue(False)

    @unittest.skip
    def test_edges_parse_xml_to_nodes_edges(self):
        (_, edges) = self.intact.parse_xml_to_nodes_edges(self.xml_file)
        self.assertTrue(False)

