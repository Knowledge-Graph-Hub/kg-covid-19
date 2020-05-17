import logging
import os
import random
import warnings
from typing import List, Union, Tuple, Optional

import pandas as pd  # type: ignore
import numpy as np  # type: ignore
from tqdm import tqdm


def make_edges(num_edges: int, nodes: str, edges: str, output_dir: str,
               train_fraction: float, validation: bool, node_types: list,
               min_degree: int, check_disconnected_nodes: bool = False) -> None:
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

    logging.info("Loading edge file %s" % edges)
    edges_df: pd.DataFrame = tsv_to_df(edges, usecols=['subject', 'object', 'relation',
                                                       'edge_label', 'provided_by'])

    logging.info("Loading node file %s" % nodes)
    nodes_df: pd.DataFrame = tsv_to_df(nodes)

    # emit warning if there are nodes in nodes tsv not present in edges tsv
    logging.info("Check for disconnected nodes: %r" % check_disconnected_nodes)
    if check_disconnected_nodes and has_disconnected_nodes(nodes_df, edges_df):
        warnings.warn("Graph has disconnected nodes")

    os.makedirs(output_dir, exist_ok=True)

    neg_edges_df: pd.DataFrame = \
        make_negative_edges(num_edges, nodes_df, edges_df, node_types)

    # make positive edges and new graph with those edges removed
    pos_edges_df: pd.DataFrame
    new_edges_df: pd.DataFrame
    pos_edges_df, new_edges_df, new_nodes_df = \
        make_positive_edges(num_edges, nodes_df, edges_df, min_degree, node_types)

    # write out new graph
    df_to_tsv(new_edges_df, new_edges_outfile)
    df_to_tsv(nodes_df, new_nodes_outfile)

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
                        edge_label: str = 'negative_edge',
                        relation: str = 'negative_edge'
                        ) -> pd.DataFrame:
    """Given a graph (as nodes and edges pandas dataframes), select num_edges edges that
    are NOT present in the graph

    :param num_edges: how many edges
    :param nodes_df: pandas dataframe containing node info
    :param edges_df: pandas dataframe containing edge info
    :param node_types: if given, we select edges involving nodes of the given types
    (not implemented yet)
    :param relation: string to put in relation column
    :param edge_label: string to put in edge_label column
    :return:
    """
    if 'subject' not in list(edges_df.columns) or 'object' not in list(edges_df.columns):
        raise ValueError("Can't find subject or object column in edges")

    if 'id' not in list(nodes_df.columns):
        raise ValueError("Can't find id column in nodes")

    edge_list = _generate_negative_edges(num_edges, nodes_df, edges_df,
                                         node_types, edge_label, relation)
    return edge_list


def _generate_negative_edges(num_edges: int,
                             nodes_df: pd.DataFrame,
                             edges_df: pd.DataFrame,
                             node_types: Optional[List[str]],
                             edge_label: str,
                             relation: str,
                             rseed: str = None) -> pd.DataFrame:
    unique_nodes = list(np.unique(np.concatenate((nodes_df.id,
                                                  edges_df.subject,
                                                  edges_df.object))))

    logging.debug("Found %i unique nodes" % len(unique_nodes))

    if rseed:
        logging.debug("Setting random seed")
        random.seed(rseed)

    logging.debug("Making random pairs of nodes (equal in size to edges)")
    random_subjects = [unique_nodes[random.randint(0, len(unique_nodes) - 1)] for _ in
                       range(edges_df.shape[0])]
    random_objects = [unique_nodes[random.randint(0, len(unique_nodes) - 1)] for _ in
                      range(edges_df.shape[0])]
    possible_edges = pd.DataFrame({'subject': random_subjects,'object': random_objects})

    logging.debug("Eliminating positives edges...")
    negative_edges = possible_edges.merge(edges_df.drop_duplicates(),
                                          on=['subject', 'object'],
                                          how='left', indicator=True)
    negative_edges = negative_edges[negative_edges['_merge'] == 'left_only']

    # two other possibilities, in case we want to refactor:
    # negative_edges = possible_edges[~possible_edges.isin(edges_df)].dropna()
    # negative_edges = possible_edges[(~possible_edges.subject.isin(edges_df.subject)
    # & ~possible_edges.object.isin(edges_df.object))]

    logging.debug("Dropping reflexive edges")
    negative_edges = \
        negative_edges[negative_edges['subject'] != negative_edges['object']]

    # theoretically might not have enough edges here
    if negative_edges.shape[0] < num_edges:
        warnings.warn("Couldn't generate %i negative edges - only %i edges left after"
                      "after removing positives and reflexives" %
                      (num_edges, negative_edges.shape[0]))

    # select only num_edges edges
    logging.debug("Selecting %i edges..." % num_edges)
    negative_edges = negative_edges.head(num_edges)

    # only subject and object
    logging.debug("Making new dataframe")
    negative_edges = negative_edges[['subject', 'object']]

    # add edge_label and relation
    negative_edges = pd.DataFrame({'subject': negative_edges['subject'],
                                   'edge_label': edge_label,
                                   'object': negative_edges['object'],
                                   'relation': relation})

    return negative_edges


def make_positive_edges(num_edges: int,
                        nodes_df: pd.DataFrame,
                        edges_df: pd.DataFrame,
                        min_degree: int,
                        node_types: list = None) -> List[Union[pd.DataFrame]]:
    """Positive edges are randomly selected from the edges in the graph, IFF both nodes
    participating in the edge have a degree greater than min_degree (to avoid creating
    disconnected components). This edge is then removed in the output graph. Negative
    edges are selected by randomly selecting pairs of nodes that are not connected by an
    edge. Optionally, if edge_type is specified, only edges between nodes of
    specified in node_types are selected.

    :param num_edges: how many edges to generate
    :param nodes_df: pandas dataframe with node info, generated from KGX TSV file
    :param edges_df: pandas dataframe with edge info, generated from KGX TSV file
    :param min_degree: the minimum degree of nodes to be selected for positive edges
    :param node_types:  if given, we select edges involving nodes of the given types
    (not implemented yet)
    :return: three pandas dataframes:
    pos_edges_df: a dataframe with positive edges,
    new_edges_df: a dataframe with edges for new graph, with positive edges we
    selected removed from graph
    """
    if 'subject' not in list(edges_df.columns) or 'object' not in list(edges_df.columns):
        raise ValueError("Can't find subject or object column in edges")

    if 'id' not in list(nodes_df.columns):
        raise ValueError("Can't find id column in nodes")

    shuffled_edges = edges_df[['subject', 'object']].sample(frac=1)

    positive_edges = pd.DataFrame(columns=['subject', 'edge_label', 'object', 'relation'])

    # iterate through shuffled edges until we get num_edges, or run out of edges
    with tqdm(total=num_edges) as pbar:
        for i in range(shuffled_edges.shape[0]):
            this_row = shuffled_edges.iloc[[i]]
            # pandas why are you like this
            to_append = [this_row['subject'].item(),
                         'positive_edge',
                         this_row['object'].item(),
                         'positive_edge']
            length = len(positive_edges)
            positive_edges.loc[len] = to_append

            pbar.update(1)

            if positive_edges.shape[0] == num_edges:
                break

    new_graph_edges = edges_df.head(edges_df.shape[0] - num_edges)

    return [positive_edges, new_graph_edges]


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
