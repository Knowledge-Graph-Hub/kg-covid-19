import unittest
from xml.dom import minidom

from parameterized import parameterized

from kg_covid_19.transform_utils.intact.intact import IntAct


class TestIntAct(unittest.TestCase):

    def setUp(self) -> None:
        self.xml_file = 'tests/resources/intact_test.xml'
        self.chebi_test_xml = \
            'tests/resources/31315999_weird_chebi_id.xml'  # weird odd CHEBI id
        self.intact = IntAct()

    def test_struct_parse_xml_to_nodes_edges(self):
        parsed = self.intact.parse_xml_to_nodes_edges(self.xml_file)
        self.assertTrue(isinstance(parsed, dict))
        self.assertTrue(isinstance(parsed['nodes'], list))
        self.assertTrue(isinstance(parsed['edges'], list))

    def test_nodes_parse_xml_to_nodes_edges(self):
        parsed = self.intact.parse_xml_to_nodes_edges(self.xml_file)
        self.assertTrue('nodes' in parsed)
        self.assertEqual(len(parsed['nodes']), 5,
                         "Didn't get the expected number of nodes")
        self.assertEqual(parsed['nodes'][0],
                              ['UniProtKB:P20290', 'btf3_human', 'biolink:Protein'])
        # one xml contains an RNA interaction, so let's test that
        # we parse that correctly
        self.assertEqual(parsed['nodes'][1],
                              ['UniProtKB:P0C6X7-PRO_0000037317', 'nsp10_cvhsa',
                               'biolink:RNA'])

    def test_edges_parse_xml_to_nodes_edges(self):
        parsed = self.intact.parse_xml_to_nodes_edges(self.xml_file)
        self.assertTrue('edges' in parsed)
        self.assertEqual(len(parsed['edges']), 8,
                         "Didn't get the expected number of edges")
        self.assertEqual(parsed['edges'][0],
                              ['UniProtKB:P20290',
                               'biolink:interacts_with',
                               'UniProtKB:P0C6X7-PRO_0000037317',
                               'RO:0002437',
                               '2',
                               'physical association',
                               '2 hybrid',
                               'PMID:16157265'
                               ])

    def test_fix_for_chebi_id(self):
        parsed = self.intact.parse_xml_to_nodes_edges(self.chebi_test_xml)
        self.assertEqual(parsed['nodes'][0][0], 'CHEBI:28304')
        self.assertEqual(parsed['edges'][0][0], 'CHEBI:28304')

    @parameterized.expand([
        ('3674925', {'publication': 'PMID:16157265', 'detection_method': '2 hybrid'}),
        ('3674926', {'publication': 'PMID:16157265', 'detection_method': '2 hybrid'})
    ])
    def test_parse_experiment_info(self, exp_id, correct_data):
        xmldoc = minidom.parse(self.xml_file)
        parsed = self.intact.parse_experiment_info(xmldoc)
        self.assertTrue(isinstance(parsed, dict))
        self.assertTrue(exp_id in parsed)
        for key, _ in correct_data.items():
            self.assertTrue(key in parsed[exp_id])
            self.assertEqual(parsed[exp_id][key], correct_data[key])
