import unittest

import pandas as pd
from pandas import np

from kg_covid_19.edges import make_edges, tsv_to_df, has_disconnected_nodes, \
    make_negative_edges


class TestEdges(unittest.TestCase):
    def setUp(self) -> None:
        self.small_nodes_file = 'tests/resources/edges/small_graph_nodes.tsv'
        self.small_edges_file = 'tests/resources/edges/small_graph_edges.tsv'

    def test_tsv_to_df(self):
        df = tsv_to_df(self.small_edges_file)
        self.assertTrue(isinstance(df, pd.DataFrame))
        self.assertEqual((21, 5), df.shape)
        self.assertEqual(df['subject'][0], 'g1')

    def test_make_edges(self):
        self.assertTrue(True)

    def test_has_disconnected_nodes(self):
        edges = tsv_to_df(self.small_edges_file)
        nodes = tsv_to_df(self.small_nodes_file)
        nodes_extra = tsv_to_df('tests/resources/edges/small_graph_nodes_EXTRA_IDS.tsv')
        self.assertTrue(not has_disconnected_nodes(edges_df=edges, nodes_df=nodes))
        self.assertTrue(has_disconnected_nodes(edges_df=edges, nodes_df=nodes_extra))

    def test_make_negative_edges(self):
        num_edges = 5
        expected_columns = ['subject', 'edge_label', 'object', 'relation']
        expected_edge_label = 'negative_edge'
        expected_relation = 'negative_edge'
        edges = tsv_to_df(self.small_edges_file)
        nodes = tsv_to_df(self.small_nodes_file)
        unique_node_ids = list(np.unique(nodes.id))

        neg_edge_df = make_negative_edges(num_edges=num_edges, edges_df=edges,
                                          nodes_df=nodes)
        self.assertTrue(isinstance(neg_edge_df, pd.DataFrame))
        self.assertEqual(num_edges, neg_edge_df.shape[0])
        self.assertEqual(len(expected_columns), neg_edge_df.shape[1],
                         "didn't get expected columns in negative edge df")
        self.assertListEqual(expected_columns, list(neg_edge_df.columns))
        self.assertListEqual([expected_edge_label] * neg_edge_df.shape[0],
                             list(neg_edge_df.edge_label),
                             "Edge label column not correct")
        self.assertListEqual([expected_relation] * neg_edge_df.shape[0],
                             list(neg_edge_df.relation),
                             "Relation column not correct")

        neg_nodes = list(np.unique(np.concatenate((neg_edge_df.subject,
                                                   neg_edge_df.object))))
        self.assertTrue(set(neg_nodes) <= set(unique_node_ids),
                        "Some nodes from negative edges are not in the nodes tsv file")
        # test node_types


