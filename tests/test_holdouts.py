import os
import tempfile
import unittest

import pandas as pd
from numpy import NaN
from pandas import np
from parameterized import parameterized

from kg_covid_19.make_holdouts import make_holdouts, tsv_to_df, make_negative_edges, \
    make_positive_edges, df_to_tsv


class TestEdges(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.nodes_file = 'tests/resources/holdouts/bigger_graph_nodes.tsv'
        cls.edges_file = 'tests/resources/holdouts/bigger_graph_edges.tsv'
        cls.edges = tsv_to_df(cls.edges_file)
        cls.nodes = tsv_to_df(cls.nodes_file)

        # make negative edges for small graph
        cls.ne = make_negative_edges(nodes_df=cls.nodes, edges_df=cls.edges)

        # make positive edges for small graph
        cls.train_fraction = 0.8
        (cls.train_edges, cls.test_edges) = make_positive_edges(
            nodes_df=cls.nodes, edges_df=cls.edges, train_fraction= cls.train_fraction)

    def setUp(self) -> None:
        pass

    def test_tsv_to_df(self):
        df = tsv_to_df(self.edges_file)
        self.assertTrue(isinstance(df, pd.DataFrame))
        self.assertEqual((150, 5), df.shape)
        self.assertEqual(df['subject'][0], 'g1')

    def test_df_to_tsv(self):
        path = os.path.join(tempfile.mkdtemp(), 'some.tsv')
        df = tsv_to_df(self.edges_file)
        df_to_tsv(df, path)
        self.assertTrue(os.path.isfile(path))
        df_roundtrip = tsv_to_df(path)
        self.assertEqual(df.shape, df_roundtrip.shape)

    def test_make_edges_exists(self):
        self.assertTrue(isinstance(make_holdouts, object))

    #
    # Test output files
    #

    @parameterized.expand([
        ('pos_train_edges.tsv', True, True, 0.8),
        ('pos_test_edges.tsv', True, True, 0.1),
        ('pos_test_edges.tsv', False, True, 0.2),  # no validation set
        ('pos_valid_edges.tsv', True, True, 0.1),
        ('pos_valid_edges.tsv', False, False, NaN),  # no validation set
        ('neg_train_edges.tsv', True, True, 0.8),
        ('neg_test_edges.tsv', True, True, 0.1),
        ('neg_test_edges.tsv', False, True, 0.2),  # no validation set
        ('neg_valid_edges.tsv', True, True, 0.1),
        ('neg_valid_edges.tsv', False, False, NaN),  # no validation set
    ])
    def test_make_edges_check_edge_output_files(self, output_file: str,
                                                make_validation: bool,
                                                file_should_exist: bool,
                                                expected_fract: float):
        me_output_dir = tempfile.mkdtemp()
        output_file_with_path = os.path.join(me_output_dir, output_file)
        input_edges = tsv_to_df(self.edges_file)
        num_input_edges = input_edges.shape[0]
        make_holdouts(nodes=self.nodes_file, edges=self.edges_file,
                      output_dir=me_output_dir, train_fraction=0.8,
                      validation=make_validation)
        if file_should_exist:
            self.assertTrue(os.path.isfile(output_file_with_path))
            new_edges_df = tsv_to_df(output_file_with_path)
            # make sure we get expected
            self.assertAlmostEqual(new_edges_df.shape[0],
                                   num_input_edges * expected_fract, 1)
            # should also have subject and object column
            self.assertTrue('subject' in new_edges_df)
            self.assertTrue('object' in new_edges_df)
        else:
            self.assertTrue(not os.path.isfile(output_file_with_path))

    @parameterized.expand([
        ('pos_train_edges.tsv', 'pos_test_edges.tsv', 'pos_valid_edges.tsv'),
        ('neg_train_edges.tsv', 'neg_test_edges.tsv', 'neg_valid_edges.tsv'),
    ])
    def test_make_edges_pos_train_test_valid_edges_distinct(self, train, test, valid):
        output_dir = tempfile.mkdtemp()
        input_edges = tsv_to_df(self.edges_file)
        make_holdouts(nodes=self.nodes_file, edges=self.edges_file,
                      output_dir=output_dir, train_fraction=0.8,
                      validation=True)
        input_edges = tsv_to_df(self.edges_file)[['subject', 'object']]
        train_edges = tsv_to_df(os.path.join(output_dir, train))[['subject', 'object']]
        test_edges = tsv_to_df(os.path.join(output_dir, test))[['subject', 'object']]
        valid_edges = tsv_to_df(os.path.join(output_dir, valid))[['subject', 'object']]

        # train should not share any members with test
        self.assertTrue(not set(train_edges).isdisjoint(test_edges))
        # train should not share any members with valid
        self.assertTrue(not set(train_edges).isdisjoint(valid_edges))
        # test should not share any members with valid
        self.assertTrue(not set(test_edges).isdisjoint(valid_edges))

        # train should be a subset of input_edges
        self.assertTrue(set(train_edges) <= set(input_edges))
        # test should be a subset of input_edges
        self.assertTrue(set(test_edges) <= set(input_edges))
        # valid should be a subset of input_edges
        self.assertTrue(set(valid_edges) <= set(input_edges))

    def test_make_edges_check_node_output_file(self):
        output_dir = tempfile.mkdtemp()
        output_file_with_path = os.path.join(output_dir, 'pos_train_nodes.tsv')
        input_nodes = tsv_to_df(self.nodes_file)
        make_holdouts(nodes=self.nodes_file, edges=self.edges_file,
                      output_dir=output_dir, train_fraction=0.8,
                      validation=False)
        self.assertTrue(os.path.isfile(output_file_with_path))
        new_nodes_df = tsv_to_df(output_file_with_path)
        # make sure we get expected
        self.assertAlmostEqual(new_nodes_df.shape[0], input_nodes.shape[0])
        # should also have subject and object column
        self.assertTrue('id' in new_nodes_df)
        self.assertTrue('category' in new_nodes_df)

    #
    # positive edge tests
    #

    def test_make_positives_edges_check_test_edge_instance_type(self):
        self.assertTrue(isinstance(self.test_edges, pd.DataFrame))

    def test_make_positives_edges_check_new_edges_instance_type(self):
        self.assertTrue(isinstance(self.train_edges, pd.DataFrame))

    def test_make_positive_edges_check_num_train_edges_returned(self):
        num_train_edges = self.train_edges.shape[0]
        expected_edges = self.edges.shape[0] * self.train_fraction
        self.assertTrue(abs(num_train_edges - expected_edges) <= 1,
                        "Didn't get the expected number of training edges (within 1)"
                        " - expected %i got %i" % (expected_edges, num_train_edges))

    def test_make_positive_edges_check_num_test_edges_returned(self):
        num_test_edges = self.test_edges.shape[0]
        expected_edges = self.edges.shape[0] * (1 - self.train_fraction)
        self.assertTrue(abs(num_test_edges - expected_edges) <= 1,
                        "Didn't get the expected number of test edges (within 1)"
                        " - expected %i got %i" % (expected_edges, num_test_edges))

    def test_make_positive_edges_check_train_edges_column_num(self):
        self.assertEqual(self.edges.shape[1],
                         self.train_edges.shape[1],
                         "New graph edges don't have the same number of columns"
                         "as the original")

    def test_make_positive_edges_check_train_edges_columns(self):
        self.assertListEqual(list(self.edges.columns),
                             list(self.train_edges.columns),
                             "New graph edges don't have the same columns"
                             "as the original")

    def test_make_positive_edges_check_test_edges_column_names(self):
        expected_columns = ['subject', 'edge_label', 'object', 'relation', 'weight',
                            'subj_degree', 'obj_degree']
        self.assertEqual(len(expected_columns), self.test_edges.shape[1],
                         "didn't get expected columns in positive edge df")
        self.assertListEqual(expected_columns, list(self.test_edges.columns))

    def test_make_positive_edges_check_test_edge_label_column(self):
        expected_edge_label = 'positive_edge'
        self.assertListEqual([expected_edge_label] * self.test_edges.shape[0],
                             list(self.test_edges.edge_label),
                             "Edge label column not correct in positive edges")

    def test_make_positive_edges_check_test_edge_relation_column(self):
        expected_relation = 'positive_edge'
        self.assertListEqual([expected_relation] * self.test_edges.shape[0],
                             list(self.test_edges.relation),
                             "Relation column not correct in positive edges")

    def test_make_positive_edges_check_nodes(self):
        unique_node_ids = list(np.unique(self.nodes.id))
        pos_nodes = list(np.unique(np.concatenate((self.test_edges.subject,
                                                   self.test_edges.object))))
        self.assertTrue(set(pos_nodes) <= set(unique_node_ids),
                        "Some nodes from positive edges are not in the nodes tsv file")

    def test_make_positive_edges_test_repeated_edges(self):
        count_info = self.test_edges.groupby(['subject', 'object']).size().\
            reset_index().rename(columns={0: 'counts'})
        dup_rows = count_info.loc[count_info.counts > 1]
        dup_rows_str = dup_rows.to_string(index=False, index_names=False)
        self.assertTrue(dup_rows.shape[0] == 0,
                        "Got %i duplicated edges:\n%s" % (dup_rows.shape[0],
                                                          dup_rows_str))

    def test_make_positive_edges_test_pos_edges_are_in_input_edge_df(self):
        overlap_pe_edges = self.test_edges.merge(self.edges, on=['subject', 'object'])
        self.assertEqual(overlap_pe_edges.shape[0], self.test_edges.shape[0],
                         "%i rows in positive edges aren't in original edges: %s" %
                         (overlap_pe_edges.shape[0], overlap_pe_edges.to_string()))

    def test_make_positive_edges_test_pos_edges_are_removed_from_train_edges(self):
        overlap_test_train = self.test_edges.merge(self.train_edges,
                                                   on=['subject', 'object'])
        self.assertEqual(overlap_test_train.shape[0], 0,
                         "%i rows in positive edges were not removed from new edges: %s"
                         % (overlap_test_train.shape[0],
                            overlap_test_train.to_string()))

    #
    # negative edge tests
    #
    def test_make_negative_edges_check_instance_type(self):
        self.assertTrue(isinstance(self.ne, pd.DataFrame))

    def test_make_negative_edges_check_num_edges_returned(self):
        # make sure we don't create duplicate negative edges
        repeat_test = 20  # repeat to ensure we aren't sometimes truncating
        for _ in range(repeat_test):
            ne = make_negative_edges(nodes_df=self.nodes, edges_df=self.edges)
            self.assertEqual(self.edges.shape[0], ne.shape[0])

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



