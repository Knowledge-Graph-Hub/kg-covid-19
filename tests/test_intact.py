import unittest
from xml.dom import minidom

from parameterized import parameterized

from kg_covid_19.transform_utils.intact.intact import IntAct


class TestIntAct(unittest.TestCase):

    def setUp(self) -> None:
        self.intact = IntAct()

    def test_intact_instance(self):
        self.assertEqual(self.intact.node_header,
                         ['id', 'name', 'category', 'ncbi_taxid', 'provided_by'])
        self.assertEqual(self.intact.edge_header,
                        ['subject', 'edge_label', 'object', 'relation', 'provided_by', 'type',
                         'publication', 'num_participants', 'association_type',
                         'detection_method', 'subj_exp_role', 'obj_exp_role'])

    def test_struct_parse_xml_to_nodes_edges(self):
        parsed = self.intact.parse_xml_to_nodes_edges('tests/resources/intact_test.xml')
        self.assertTrue(isinstance(parsed, dict))
        self.assertTrue(isinstance(parsed['nodes'], list))
        self.assertTrue(isinstance(parsed['edges'], list))

    @parameterized.expand([
        ('tests/resources/intact_test.xml',
         5, 8,  # node and edge count, respectively
         # nodes and edges given here are checked against the first values in
         # parsed['nodes'] and parsed['edges']. Extra items in parsed['nodes'] and
         # parsed['edges'] are ignored
         {'nodes': [['UniProtKB:P20290', 'btf3_human', 'biolink:Protein', '9606', 'intact'],
                    ['UniProtKB:P0C6X7-PRO_0000037317', 'nsp10_cvhsa', 'biolink:RNA',
                     '694009', 'intact']],
          'edges': [['UniProtKB:P20290', 'biolink:interacts_with',
                     'UniProtKB:P0C6X7-PRO_0000037317', 'RO:0002437', 'intact', 'biolink:Association',
                     'PMID:16157265', '2', 'physical association', '2 hybrid', 'prey',
                     'bait']]
         }),
        ('tests/resources/intact_3_participants.xml',  # test interactions with 3 participants
         3, 3,  # interaction with 3 participants yields 3 edges (1<->2, 2<->3, 1<->3)
         {'nodes': [],
          'edges': [['UniProtKB:Q3T133',
                'biolink:interacts_with',
                'UniProtKB:P41811',
                'RO:0002437',
                'intact',
                'biolink:Association',
                'PMID:23481256',
                '3',
                'physical association',
                'itc', 'neutral component', 'bait']]
          })
    ])
    def test_nodes_parse_xml_to_nodes_edges(self, xml_file, node_count, edge_count,
                                            expect_nodes_edges):
        parsed = self.intact.parse_xml_to_nodes_edges(xml_file)
        self.assertEqual(node_count, len(parsed['nodes']),
                         "Didn't get the expected number of nodes")
        self.assertEqual(edge_count, len(parsed['edges']),
                         "Didn't get the expected number of edges")
        self.assertEqual(expect_nodes_edges['nodes'],
                         parsed['nodes'][:len(expect_nodes_edges['nodes'])])
        self.assertEqual(expect_nodes_edges['edges'],
                         parsed['edges'][:len(expect_nodes_edges['edges'])])

    @parameterized.expand([
        ('tests/resources/intact_test.xml', '3674925', {'publication': 'PMID:16157265', 'detection_method': '2 hybrid'}),
        ('tests/resources/intact_test.xml', '3674926', {'publication': 'PMID:16157265', 'detection_method': '2 hybrid'})
    ])
    def test_parse_experiment_info(self, xml_file, exp_id, correct_data):
        xmldoc = minidom.parse(xml_file)
        parsed = self.intact.parse_experiment_info(xmldoc)
        self.assertTrue(isinstance(parsed, dict))
        self.assertTrue(exp_id in parsed)
        for key, _ in correct_data.items():
            self.assertTrue(key in parsed[exp_id])
            self.assertEqual(parsed[exp_id][key], correct_data[key])

    def test_fix_for_chebi_id(self):
        chebi_test_xml = 'tests/resources/31315999_weird_chebi_id.xml'  # weird CHEBI id
        parsed = self.intact.parse_xml_to_nodes_edges(chebi_test_xml)
        self.assertEqual(parsed['nodes'][0][0], 'CHEBI:28304')
        self.assertEqual(parsed['edges'][0][0], 'CHEBI:28304')
