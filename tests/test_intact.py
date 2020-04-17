import unittest

from kg_covid_19.transform_utils.intact.intact import IntAct


class TestIntAct(unittest.TestCase):

    def setUp(self) -> None:
        self.xml_file = 'tests/resources/intact_test_16157265.xml'
        self.intact = IntAct()

    def test_struct_parse_xml_to_nodes_edges(self):
        parsed = self.intact.parse_xml_to_nodes_edges(self.xml_file)
        self.assertTrue(isinstance(parsed, dict))
        self.assertTrue(isinstance(parsed['nodes'], list))
        self.assertTrue(isinstance(parsed['edges'], list))

    def test_nodes_parse_xml_to_nodes_edges(self):
        (nodes, _) = self.intact.parse_xml_to_nodes_edges(self.xml_file)
        # <shortLabel>btf3_human</shortLabel>
        # <primaryRef db="uniprotkb" dbAc="MI:0486" id="P20290" version="SP_65" refType="identity" refTypeAc="MI:0356"/>
        # <shortLabel>nsp10_cvhsa</shortLabel>
        # <primaryRef db="uniprotkb" dbAc="MI:0486" id="P0C6X7-PRO_0000037317" refType="identity" refTypeAc="MI:0356"/>
        # <shortLabel>protein</shortLabel>
        # <shortLabel>nu4lm_human</shortLabel>
        # <primaryRef db="uniprotkb" dbAc="MI:0486" id="P03901" version="SP_73" refType="identity" refTypeAc="MI:0356"/>
        # <shortLabel>cox2_human</shortLabel>
        # <primaryRef db="uniprotkb" dbAc="MI:0486" id="P00403" version="SP_95" refType="identity" refTypeAc="MI:0356"/>
        # <shortLabel>atf5_human</shortLabel>
        # <primaryRef db="uniprotkb" dbAc="MI:0486" id="Q9Y2D1" version="SP_67" refType="identity" refTypeAc="MI:0356"/>
        self.assertEqual(len(nodes), 5, "Didn't get the expected number of nodes")

    @unittest.skip
    def test_edges_parse_xml_to_nodes_edges(self):
        (_, edges) = self.intact.parse_xml_to_nodes_edges(self.xml_file)
        self.assertTrue(False)

