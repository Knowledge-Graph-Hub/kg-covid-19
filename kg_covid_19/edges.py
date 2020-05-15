import logging
import os

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
        :param min_degree:

    """
    edges_df = tsv_to_df(edges)
    nodes_df = tsv_to_df(nodes)

    # emit warning if there are nodes in nodes tsv not present in edges tsv
    if has_disconnected_nodes(nodes_df, edges_df):
        logging.warning("Graph has disconnected nodes")

    os.makedirs(output_dir, exist_ok=True)

    # make positive edges


    # Positive edges are randomly selected from the edges in the graph, IFF both nodes
    # participating in the edge have a degree greater than min_degree (to avoid creating
    # disconnected components). This edge is then removed in the output graph. Negative
    # edges are selected by randomly selecting pairs of nodes that are not connected by an
    # edge. Optionally, if edge_type is specified, only edges between nodes of
    # specified in node_types are selected.
    #
    # For both positive and negative edge sets, edges are assigned to training set
    # according to train_fraction (0.8 by default). The remaining are assigned to test set
    # or split evenly between test and validation set, if [validation==True].

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
