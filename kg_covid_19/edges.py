import logging
import os
import random
import warnings
from typing import List, Union, Tuple, Optional

import pandas as pd  # type: ignore
import numpy as np  # type: ignore
from tqdm import tqdm  # type: ignore


def make_edges(nodes: str, edges: str, output_dir: str,
               train_fraction: float, validation: bool,
               min_degree: int, check_disconnected_nodes: bool = False) -> None:
    """Prepare positive and negative edges for testing and training (see run.py edges
    command for documentation)

    Args:
        :param nodes    nodes of input graph, in KGX TSV format [data/merged/nodes.tsv]
        :param edges:   edges for input graph, in KGX TSV format [data/merged/edges.tsv]
        :param output_dir:     directory to output edges and new graph [data/edges/]
        :param train_fraction: fraction of edges to emit as training
        :param validation:     should we make validation edges? [False]
        :param min_degree      when choosing positive edges, what is the minimum degree
                        of nodes involved in the edge [2]
        :param check_disconnected_nodes: should we check for disconnected nodes (i.e.
                        nodes with degree of 0) in input graph? [False]
    Returns:
        None.
    """
    pos_train_edges_outfile = os.path.join(output_dir, "pos_train_edges.tsv")
    pos_train_nodes_outfile = os.path.join(output_dir, "pos_train_nodes.tsv")

    logging.info("Loading edge file %s" % edges)
    edges_df: pd.DataFrame = tsv_to_df(edges, usecols=['subject', 'object', 'relation',
                                                       'edge_label'])
    logging.info("Loading node file %s" % nodes)
    nodes_df: pd.DataFrame = tsv_to_df(nodes)

    # emit warning if there are nodes in nodes tsv not present in edges tsv
    logging.info("Check for disconnected nodes: %r" % check_disconnected_nodes)
    if check_disconnected_nodes and has_disconnected_nodes(nodes_df, edges_df):
        warnings.warn("Graph has disconnected nodes")

    os.makedirs(output_dir, exist_ok=True)

    # make positive edges
    pos_train_edges: pd.DataFrame
    pos_test_edges: pd.DataFrame
    pos_train_edges, pos_test_edges = \
        make_positive_edges(nodes_df=nodes_df,
                            edges_df=edges_df,
                            train_fraction=train_fraction,
                            min_degree=min_degree)

    # make negative edges
    neg_edges_df: pd.DataFrame = make_negative_edges(nodes_df, edges_df)

    # write out positive edges
    df_to_tsv(pos_train_edges, pos_train_edges_outfile)
    df_to_tsv(pos_test_edges, pos_train_nodes_outfile)

    # write out negative edges
    write_edge_files(neg_edges_df, train_fraction, validation, "neg")

    # write out positive edges
    write_edge_files(pos_edges_df, train_fraction, validation, "pos")


def df_to_tsv(new_edges_df, new_edges_outfile) -> None:
    raise NotImplementedError


def make_negative_edges(nodes_df: pd.DataFrame,
                        edges_df: pd.DataFrame,
                        edge_label: str = 'negative_edge',
                        relation: str = 'negative_edge'
                        ) -> pd.DataFrame:
    """Given a graph (as nodes and edges pandas dataframes), select num_edges edges that
    are NOT present in the graph

    :param nodes_df: pandas dataframe containing node info
    :param edges_df: pandas dataframe containing edge info
    :param relation: string to put in relation column
    :param edge_label: string to put in edge_label column
    :return:
    """
    if 'subject' not in list(edges_df.columns) or 'object' not in list(edges_df.columns):
        raise ValueError("Can't find subject or object column in edges")

    if 'id' not in list(nodes_df.columns):
        raise ValueError("Can't find id column in nodes")

    edge_list = _generate_negative_edges(nodes_df=nodes_df, edges_df=edges_df,
                                         edge_label=edge_label, relation=relation)
    return edge_list


def _generate_negative_edges(nodes_df: pd.DataFrame,
                             edges_df: pd.DataFrame,
                             edge_label: str,
                             relation: str,
                             rseed: str = None) -> pd.DataFrame:
    if rseed:
        logging.debug("Setting random seed")
        random.seed(rseed)

    with tqdm(total=8) as pbar:
        unique_nodes = list(np.unique(np.concatenate((nodes_df.id,
                                                      edges_df.subject,
                                                      edges_df.object))))
        pbar.update()

        pbar.set_description("Making random pairs of nodes")
        random_subjects = [unique_nodes[random.randint(0, len(unique_nodes) - 1)]
                           for _ in range(2 * edges_df.shape[0])]
        random_objects = [unique_nodes[random.randint(0, len(unique_nodes) - 1)]
                          for _ in range(2 * edges_df.shape[0])]
        possible_edges = pd.DataFrame({'subject': random_subjects,
                                       'object': random_objects})
        pbar.update()

        pbar.set_description("Eliminating duplicated negative edges")
        possible_edges.drop_duplicates(subset=['subject', 'object'], keep=False,
                                       inplace=True)
        pbar.update()

        pbar.set_description("Eliminating positives edges")
        negative_edges = possible_edges.merge(edges_df.drop_duplicates(),
                                              on=['subject', 'object'],
                                              how='left', indicator=True)
        negative_edges = negative_edges[negative_edges['_merge'] == 'left_only']
        pbar.update()

        pbar.set_description("Dropping reflexive edges")
        negative_edges = \
            negative_edges[negative_edges['subject'] != negative_edges['object']]
        pbar.update()

        pbar.set_description("Selecting %i edges..." % edges_df.shape[0])
        # theoretically might not have enough edges here
        if negative_edges.shape[0] < edges_df.shape[0]:
            warnings.warn("Couldn't generate %i negative edges - only %i edges left "
                          "after removing positives and reflexives" %
                          (edges_df.shape[0], negative_edges.shape[0]))
            negative_edges = negative_edges.head(negative_edges.shape[0])
        else:
            # select only num_edges edges
            negative_edges = negative_edges.head(edges_df.shape[0])
        pbar.update()

        # only subject and object
        pbar.set_description("Making new dataframe")
        negative_edges = negative_edges[['subject', 'object']]
        pbar.update()

        # add edge_label and relation
        negative_edges = pd.DataFrame({'subject': negative_edges['subject'],
                                       'edge_label': edge_label,
                                       'object': negative_edges['object'],
                                       'relation': relation})
        pbar.update()

    return negative_edges


def make_positive_edges(nodes_df: pd.DataFrame,
                        edges_df: pd.DataFrame,
                        train_fraction: float,
                        min_degree: int) -> List[pd.DataFrame]:
    """Positive edges are randomly selected from the edges in the graph, IFF both nodes
    participating in the edge have a degree greater than min_degree (to avoid creating
    disconnected components). This edge is then removed in the output graph. Negative
    edges are selected by randomly selecting pairs of nodes that are not connected by an
    edge.

    :param nodes_df: pandas dataframe with node info, generated from KGX TSV file
    :param edges_df: pandas dataframe with edge info, generated from KGX TSV file
    :param train_fraction: fraction of input edges to emit as test (and optionally
                  validation) edges
    :param min_degree: the minimum degree of nodes to be selected for positive edges
    :return:  pandas dataframes:
    training_edges_df: a dataframe with training edges with positive edges we
                    selected for test removed from graph
    test_edges_df: a dataframe with training edges with positive edges
    """
    if 'subject' not in list(edges_df.columns) or \
            'object' not in list(edges_df.columns):
        raise ValueError("Can't find subject or object column in edges")

    if 'id' not in list(nodes_df.columns):
        raise ValueError("Can't find id column in nodes")

    with tqdm(total=7) as pbar:
        pbar.set_description("Copying edges")
        test_edges = edges_df.copy(deep=True)
        pbar.update()

        # count degrees
        pbar.set_description("Calculating degrees")
        subj_degree = edges_df['subject'].value_counts()
        subj_degree_df = pd.DataFrame({'subject': list(subj_degree.index),
                                       'subj_degree': list(subj_degree.values)})
        obj_degree = edges_df['object'].value_counts()
        obj_degree_df = pd.DataFrame({'object': list(obj_degree.index),
                                      'obj_degree': list(obj_degree.values)})
        pbar.update()

        pbar.set_description("Merging degrees")
        test_edges = test_edges.merge(subj_degree_df, how='left', on='subject')
        test_edges = test_edges.merge(obj_degree_df, how='left', on='object')
        pbar.update()

        pbar.set_description("Removing edges < min_degree")
        test_edges.drop(test_edges[test_edges['subj_degree'] < min_degree].index,
                        inplace=True)
        test_edges.drop(test_edges[test_edges['obj_degree'] < min_degree].index,
                        inplace=True)
        pbar.update()

        pbar.set_description("Adding edge_label and relation columns")
        test_edges = test_edges.sample(frac=(1-train_fraction))
        test_edges['edge_label'] = 'positive_edge'
        test_edges['relation'] = 'positive_edge'
        pbar.update()

        pbar.set_description("Making training edges")
        train_edges = edges_df.copy(deep=True)
        pbar.update()

        pbar.set_description("Removing test edges from training data")
        train_edges.drop(train_edges.index[test_edges.index], inplace=True)
        pbar.update()

    return [train_edges, test_edges]


def write_edge_files(edges_df: pd.DataFrame,
                     train_fraction: float,
                     validation: bool,
                     prefix: str,
                     train_str: str = "train",
                     test_str: str = "test",
                     valid_str: str = "valid",
                     sep: str = "_",
                     suffix: str = ".tsv") -> None:
    """Write out edges (training, testing, validation if validation == True)

    :param edges_df: pandas dataframe with edge data
    :param train_fraction: fraction of data to use for training
    :param validation: should we write validation edges? (if so, split
                        edges evenly between test and validation)
    :param prefix: prefix for out file
    :param train_str: string to use for training file name
    :param test_str: string to use for test file name
    :param valid_str: string to use for valid file name
    :param sep: separator
    :param suffix: suffix for file name
    :return: None
    """
    raise NotImplementedError


def write_positive_edges(pos_edges_df: pd.DataFrame, train_fraction, validation):
    raise NotImplementedError


def has_disconnected_nodes(nodes_df: pd.DataFrame, edges_df: pd.DataFrame,
                           check_nodes_in_edge_df_not_in_node_df=True) -> bool:
    """Given nodes and edges df, determine if there are nodes that are not present in
    edges (disconnected vertices)

    :param nodes_df: pandas dataframe with node info
    :param edges_df: pandas dataframe with edge info
    :param check_nodes_in_edge_df_not_in_node_df: while we're at it, check if
            edge df has nodes not mentioned in node df [True]
    :return: bool
    """
    nodes_in_edge_file = \
        np.sort(np.unique(np.concatenate((edges_df.subject, edges_df.object))))
    nodes_in_node_file = np.sort(nodes_df.id.unique())

    if check_nodes_in_edge_df_not_in_node_df:
        diff = len(np.setdiff1d(nodes_in_edge_file, nodes_in_node_file))
        if diff != 0:
            warnings.warn(
                "There are %i nodes in edge file that aren't in nodes file" % diff)

    # if setdiff below is zero, odes_in_node_file is a subset of nodes_in_edge_file
    if len(np.setdiff1d(nodes_in_node_file, nodes_in_edge_file)) == 0:
        return False
    else:
        return True


def tsv_to_df(tsv_file: str, *args, **kwargs) -> pd.DataFrame:
    """Read in a TSV file and return a pandas dataframe

    :param tsv_file: file to read in
    :return: pandas dataframe
    """
    df = pd.read_csv(tsv_file, sep="\t", *args, **kwargs)
    return df
