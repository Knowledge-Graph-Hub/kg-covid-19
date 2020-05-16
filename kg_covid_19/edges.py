import logging
import os
import warnings
from typing import List, Union, Tuple

import pandas as pd  # type: ignore
import numpy as np  # type: ignore


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
        warnings.warn("Graph has disconnected nodes")

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
                        node_types: list = None,
                        return_edge_columns: Tuple[str, str, str, str] =
                        ('subject', 'edge_label', 'object', 'relation'),
                        edge_label: str = 'negative_edge',
                        relation: str = 'negative_edge'
                        ) -> pd.DataFrame:
    """Given a graph (as nodes and edges pandas dataframes), select num_edges edges that
    are NOT present in the graph

    :param num_edges: how many edges
    :param nodes_df: pandas dataframe containing node info
    :param edges_df: pandas dataframe containing edge info
    :param node_types: if given, we select edges involving nodes of the given types
    :param return_edge_columns: columns in return dataframe
    :param relation: string to put in relation column
    :param edge_label: string to put in edge_label column
    :return:
    """
    if 'subject' not in list(edges_df.columns) or 'object' not in list(edges_df.columns):
        logging.error("Can't find subject or object column in edges")

    unique_nodes = list(np.unique(np.concatenate((edges_df.subject, edges_df.object))))

    completed_edges = 0
    iteration = 0
    edge_list: list = []
    while completed_edges < num_edges:
        edge_list.append(['g1', edge_label, 'g2', relation])
        completed_edges += 1

        if iteration > (10 * num_edges):
            raise RuntimeError("Too many iterations")

    return_df = pd.DataFrame(edge_list, columns=return_edge_columns)
    return return_df


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


def tsv_to_df(tsv_file: str) -> pd.DataFrame:
    """Read in a TSV file and return a pandas dataframe

    :param tsv_file: file to read in
    :return: pandas dataframe
    """
    df = pd.read_csv(tsv_file, sep="\t")
    return df
