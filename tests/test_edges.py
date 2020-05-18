import unittest

import pandas as pd
from pandas import np

from kg_covid_19.edges import make_edges, tsv_to_df, has_disconnected_nodes, \
    make_negative_edges, make_positive_edges


class TestEdges(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.small_nodes_file = 'tests/resources/edges/small_graph_nodes.tsv'
        cls.small_edges_file = 'tests/resources/edges/small_graph_edges.tsv'
        cls.edges = tsv_to_df(cls.small_edges_file)
        cls.nodes = tsv_to_df(cls.small_nodes_file)

        # make negative edges for small graph
        cls.ne = make_negative_edges(nodes_df=cls.nodes, edges_df=cls.edges)

        # make positive edges for small graph
        cls.train_fraction = 0.8
        (cls.train_edges, cls.test_edges) = make_positive_edges(
            nodes_df=cls.nodes, edges_df=cls.edges, train_fraction= cls.train_fraction,
            min_degree=1)

    def setUp(self) -> None:
        pass

    def test_tsv_to_df(self):
        df = tsv_to_df(self.small_edges_file)
        self.assertTrue(isinstance(df, pd.DataFrame))
        self.assertEqual((21, 5), df.shape)
        self.assertEqual(df['subject'][0], 'g1')

    def test_make_edges(self):
        self.assertTrue(True)

    #
    # positive edge tests
    #
    def test_make_positives_edges_check_test_edge_instance_type(self):
        self.assertTrue(isinstance(self.test_edges, pd.DataFrame))

    def test_make_positives_edges_check_new_edges_instance_type(self):
        self.assertTrue(isinstance(self.train_edges, pd.DataFrame))

    def test_make_positive_edges_check_num_edges_returned(self):
        self.assertEqual(self., self.train_edges.shape[0])

    def test_make_positive_edges_check_new_graph_size(self):
        self.assertEqual(self.edges.shape[0] - self.num_edges,
                         self.new_graph_edges.shape[0],
                         "New graph edges aren't equal to the old graph edges minus "
                         "positive edges")

    def test_make_positive_edges_check_new_graph_column_num(self):
        self.assertEqual(self.edges.shape[1],
                         self.new_graph_edges.shape[1],
                         "New graph edges don't have the same number of columns"
                         "as the original")

    def test_make_positive_edges_check_new_graph_columns(self):
        self.assertListEqual(list(self.edges.columns),
                             list(self.new_graph_edges.columns),
                             "New graph edges don't have the same columns"
                             "as the original")

    def test_make_positive_edges_check_column_names(self):
        expected_columns = ['subject', 'edge_label', 'object', 'relation']
        self.assertEqual(len(expected_columns), self.pe.shape[1],
                         "didn't get expected columns in positive edge df")
        self.assertListEqual(expected_columns, list(self.pe.columns))

    def test_make_positive_edges_check_edge_label_column(self):
        expected_edge_label = 'positive_edge'
        self.assertListEqual([expected_edge_label] * self.pe.shape[0],
                             list(self.pe.edge_label),
                             "Edge label column not correct in positive edges")

    def test_make_positive_edges_check_relation_column(self):
        expected_relation = 'positive_edge'
        self.assertListEqual([expected_relation] * self.pe.shape[0],
                             list(self.pe.relation),
                             "Relation column not correct in positive edges")

    def test_make_positive_edges_check_nodes(self):
        unique_node_ids = list(np.unique(self.nodes.id))
        pos_nodes = list(np.unique(np.concatenate((self.pe.subject,
                                                   self.pe.object))))
        self.assertTrue(set(pos_nodes) <= set(unique_node_ids),
                        "Some nodes from positive edges are not in the nodes tsv file")

    def test_make_positive_edges_test_repeated_edges(self):
        count_info = self.pe.groupby(['subject', 'object']).size().\
            reset_index().rename(columns={0: 'counts'})
        dup_rows = count_info.loc[count_info.counts > 1]
        dup_rows_str = dup_rows.to_string(index=False, index_names=False)
        self.assertTrue(dup_rows.shape[0] == 0,
                        "Got %i duplicated edges:\n%s" % (dup_rows.shape[0],
                                                          dup_rows_str))

    def test_make_positive_edges_test_pos_edges_are_in_edge_df(self):
        overlap_pe_edges = self.pe.merge(self.edges, on=['subject', 'object'])
        self.assertEqual(overlap_pe_edges.shape[0], self.pe.shape[0],
                         "%i rows in positive edges aren't in original edges: %s" %
                         (overlap_pe_edges.shape[0], overlap_pe_edges.to_string()))

    def test_make_positive_edges_test_pos_edges_are_not_in_new_edges(self):
        overlap_pe_new_edges = self.pe.merge(self.edges, on=['subject', 'object'])
        self.assertEqual(overlap_pe_new_edges.shape[0],
                         self.pe.shape[0],
                         "%i rows in positive edges were not removed from new edges: %s"
                         % (overlap_pe_new_edges.shape[0],
                            overlap_pe_new_edges.to_string()))

    #
    # negative edge tests
    #
    def test_has_disconnected_nodes(self):
        nodes_extra_ids = tsv_to_df(
            'tests/resources/edges/small_graph_nodes_EXTRA_IDS.tsv')
        nodes_missing_ids = tsv_to_df(
            'tests/resources/edges/small_graph_nodes_MISSING_IDS.tsv')
        self.assertTrue(not has_disconnected_nodes(edges_df=self.edges,
                                                   nodes_df=self.nodes))
        with self.assertWarns(Warning):
            self.assertTrue(not has_disconnected_nodes(edges_df=self.edges,
                                                       nodes_df=nodes_missing_ids))
        self.assertTrue(has_disconnected_nodes(edges_df=self.edges,
                                               nodes_df=nodes_extra_ids))

    def test_make_negative_edges_check_instance_type(self):
        self.assertTrue(isinstance(self.ne, pd.DataFrame))

    def test_make_negative_edges_check_num_edges_returned(self):
        self.assertEqual(self.edges.shape[0], self.ne.shape[0])

    def test_make_negative_edges_check_column_names(self):
        expected_columns = ['subject', 'edge_label', 'object', 'relation']
        self.assertEqual(len(expected_columns), self.ne.shape[1],
                         "didn't get expected columns in negative edge df")
        self.assertListEqual(expected_columns, list(self.ne.columns))

    def test_make_negative_edges_check_edge_label_column(self):
        expected_edge_label = 'negative_edge'
        self.assertListEqual([expected_edge_label] * self.ne.shape[0],
                             list(self.ne.edge_label),
                             "Edge label column not correct")

    def test_make_negative_edges_check_relation_column(self):
        expected_relation = 'negative_edge'
        self.assertListEqual([expected_relation] * self.ne.shape[0],
                             list(self.ne.relation),
                             "Relation column not correct")

    def test_make_negative_edges_check_neg_nodes(self):
        unique_node_ids = list(np.unique(self.nodes.id))
        neg_nodes = list(np.unique(np.concatenate((self.ne.subject,
                                                   self.ne.object))))
        self.assertTrue(set(neg_nodes) <= set(unique_node_ids),
                        "Some nodes from negative edges are not in the nodes tsv file")

    def test_make_negative_edges_no_reflexive_edges(self):
        reflexive_es = self.ne.loc[(self.ne['subject'] == self.ne['object'])]
        self.assertEqual(0, reflexive_es.shape[0],
                         "%i edges are reflexive" % reflexive_es.shape[0])

    def test_make_negative_edges_test_repeated_edges(self):
        # make sure we don't create duplicate negative edges
        repeat_test = 20  # repeat to ensure we aren't sometimes generating dups
        for _ in range(repeat_test):
            ne = make_negative_edges(nodes_df=self.nodes, edges_df=self.edges)
            count_info = ne.groupby(['subject', 'object']).size().\
                reset_index().rename(columns={0: 'counts'})
            dup_rows = count_info.loc[count_info.counts > 1]
            dup_rows_str = dup_rows.to_string(index=False, index_names=False)
            self.assertTrue(dup_rows.shape[0] == 0,
                            "Got %i duplicated edges:\n%s" % (dup_rows.shape[0],
                                                              dup_rows_str))

    def test_make_negative_edges_ensure_neg_edges_are_actually_negative(self):
        # make sure our negative edges are actually negative, i.e. not in edges_df
        non_neg_edges = self.ne.merge(self.edges, how='inner',
                                      left_on=['subject', 'object'],
                                      right_on=['subject', 'object'])
        non_neg_edges_str = non_neg_edges.to_string(index=False, index_names=False)
        self.assertTrue(non_neg_edges.shape[0] == 0,
                        "Got %i negative edges that are not actually negative:\n%s" %
                        (non_neg_edges.shape[0], non_neg_edges_str))

    # TODO - test node_types fxn


