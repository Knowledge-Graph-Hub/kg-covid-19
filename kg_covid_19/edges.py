import logging
import os
from typing import List, Union

import pandas as pd
import numpy as np


def make_edges(num_edges: int, nodes: str, edges: str, output_dir: str,
               train_fraction: float, validation: bool, node_types: list,
               min_degree: int, check_disconnected_nodes: bool = True) -> None:
    """Prepare positive and negative edges for testing and training

    Args:
        :param num_edges      number of positive and negative edges to emit
        :param nodes     nodes of input graph, in KGX TSV format [data/merged/nodes.tsv]
        :param edges:   edges for input graph, in KGX TSV format [data/merged/edges.tsv]
        :param output_dir:     directory to output edges and new graph [data/edges/]
        :param train_fraction: fraction of edges to emit as training [0.8]
        :param validation:     should we make validation edges? [False]
        :param min_degree      when choosing edges, what is the minimum degree of nodes
                        involved in the edge [1]
        :param node_types:    what node types should we make edges from? by default, any
                        type. If specified, should use items from 'category' column
        :param check_disconnected_nodes: should we check for disconnected nodes? [True]
    Returns:
        None.
    """
    new_edges_outfile = os.path.join(output_dir, "edges.tsv")
    new_nodes_outfile = os.path.join(output_dir, "nodes.tsv")

    edges_df: pd.DataFrame = tsv_to_df(edges)
    nodes_df: pd.DataFrame = tsv_to_df(nodes)

    # emit warning if there are nodes in nodes tsv not present in edges tsv
    if check_disconnected_nodes and has_disconnected_nodes(nodes_df, edges_df):
        logging.warning("Graph has disconnected nodes")

    os.makedirs(output_dir, exist_ok=True)

    neg_edges_df: pd.DataFrame = \
        make_negative_edges(num_edges, nodes_df, edges_df, node_types)

    # make positive edges and new graph with those edges removed
    pos_edges_df: pd.DataFrame
    new_edges_df: pd.DataFrame
    new_nodes_df: pd.DataFrame
    pos_edges_df, new_edges_df, new_nodes_df = \
        make_positive_edges(num_edges, nodes_df, edges_df, node_types, min_degree)

    # write out new graph
    df_to_tsv(new_edges_df, new_edges_outfile)
    df_to_tsv(new_nodes_df, new_nodes_outfile)

    # write out negative edges
    write_edge_files(neg_edges_df, train_fraction, validation, "neg")

    # write out positive edges
    write_edge_files(pos_edges_df, train_fraction, validation, "pos")


def df_to_tsv(new_edges_df, new_edges_outfile) -> None:
    raise NotImplementedError


def make_negative_edges(num_edges: int,
                        nodes_df: pd.DataFrame,
                        edges_df: pd.DataFrame,
                        node_types: list = None) -> pd.DataFrame:
    """Given a graph (as nodes and edges pandas dataframes), select num_edges edges that
    are NOT present in the graph

    :param num_edges:
    :param nodes_df:
    :param edges_df:
    :param node_types: if given, we select edges involving nodes of the given types
    :return:
    """
    if 'subject' not in list(edges_df.columns) or 'object' not in list(edges_df.columns):
        logging.warning("Can't find subject or object column in edges")
    df = edges_df[:5]
    df = df.loc[:, ['subject', 'object']]
    return df


def make_positive_edges(num_edges: int, nodes_df: pd.DataFrame, edges_df: pd.DataFrame,
                        node_types: list, min_degree: int) -> List[Union[pd.DataFrame]]:
    # Positive edges are randomly selected from the edges in the graph, IFF both nodes
    # participating in the edge have a degree greater than min_degree (to avoid creating
    # disconnected components). This edge is then removed in the output graph. Negative
    # edges are selected by randomly selecting pairs of nodes that are not connected by an
    # edge. Optionally, if edge_type is specified, only edges between nodes of
    # specified in node_types are selected.
    raise NotImplementedError


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


def has_disconnected_nodes(nodes_df: pd.DataFrame, edges_df: pd.DataFrame) -> bool:
    """Given nodes and edges df, determine if there are nodes that are not present in
    edges

    :param nodes_df: pandas data
    :param edges_df:
    :return:
    """
    nodes_edge_file = \
        np.sort(np.unique(np.concatenate((edges_df.subject, edges_df.object))))
    nodes_node_file = np.sort(nodes_df.id.unique())
    if np.array_equal(nodes_edge_file, nodes_node_file):
        return False
    else:
        return True


def tsv_to_df(tsv_file: str) -> pd.DataFrame:
    """Read in a TSV file and return a pandas dataframe

    :param tsv_file: file to read in
    :return: pandas dataframe
    """
    df = pd.read_csv(tsv_file, sep="\t")
    return df
