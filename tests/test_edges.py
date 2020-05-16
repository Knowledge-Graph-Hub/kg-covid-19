import unittest

import pandas as pd
from pandas import np

from kg_covid_19.edges import make_edges, tsv_to_df, has_disconnected_nodes, \
    make_negative_edges


class TestEdges(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.small_nodes_file = 'tests/resources/edges/small_graph_nodes.tsv'
        cls.small_edges_file = 'tests/resources/edges/small_graph_edges.tsv'
        cls.edges = tsv_to_df(cls.small_edges_file)
        cls.nodes = tsv_to_df(cls.small_nodes_file)

        # make neg edges for small graph
        cls.num_edges = 5
        cls.neg_edge_df = make_negative_edges(cls.num_edges, cls.nodes, cls.edges)

    def setUp(self) -> None:
        pass

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
        nodes_extra_ids = tsv_to_df('tests/resources/edges/small_graph_nodes_EXTRA_IDS.tsv')
        nodes_missing_ids = tsv_to_df(
            'tests/resources/edges/small_graph_nodes_MISSING_IDS.tsv')
        self.assertTrue(not has_disconnected_nodes(edges_df=edges, nodes_df=nodes))
        with self.assertWarns(Warning):
            self.assertTrue(not has_disconnected_nodes(edges_df=edges,
                                                       nodes_df=nodes_missing_ids))
        self.assertTrue(has_disconnected_nodes(edges_df=edges,
                                               nodes_df=nodes_extra_ids))

    def test_make_negative_edges_check_instance_type(self):
        self.assertTrue(isinstance(self.neg_edge_df, pd.DataFrame))

    def test_make_negative_edges_check_num_edges_returned(self):
        self.assertEqual(self.num_edges, self.neg_edge_df.shape[0])

    def test_make_negative_edges_check_columns(self):
        expected_columns = ['subject', 'edge_label', 'object', 'relation']
        expected_edge_label = 'negative_edge'
        expected_relation = 'negative_edge'
        self.assertEqual(len(expected_columns), self.neg_edge_df.shape[1],
                         "didn't get expected columns in negative edge df")
        self.assertListEqual(expected_columns, list(self.neg_edge_df.columns))
        self.assertListEqual([expected_edge_label] * self.neg_edge_df.shape[0],
                             list(self.neg_edge_df.edge_label),
                             "Edge label column not correct")
        self.assertListEqual([expected_relation] * self.neg_edge_df.shape[0],
                             list(self.neg_edge_df.relation),
                             "Relation column not correct")

    def test_make_negative_edges_check_neg_nodes(self):
        unique_node_ids = list(np.unique(self.nodes.id))
        neg_nodes = list(np.unique(np.concatenate((self.neg_edge_df.subject,
                                                   self.neg_edge_df.object))))
        self.assertTrue(set(neg_nodes) <= set(unique_node_ids),
                        "Some nodes from negative edges are not in the nodes tsv file")


    # TODO - test node_types fxn


