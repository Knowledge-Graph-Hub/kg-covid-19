"""Functions for producing holdouts for graph ML."""

import logging
import os
import random
import warnings
from typing import List, Optional

import numpy as np  # type: ignore
import pandas as pd  # type: ignore
from ensmallen import Graph
from tqdm import tqdm  # type: ignore


def make_holdouts(
    nodes: str,
    edges: str,
    output_dir: str,
    train_fraction: float,
    validation: bool,
    seed=42,
) -> None:
    """Prepare positive and negative edges for testing and training.

    (See run.py holdouts command for documentation.)
    Args:
        :param nodes    nodes of input graph, in KGX TSV format [data/merged/nodes.tsv]
        :param edges:   edges for input graph, in KGX TSV format [data/merged/edges.tsv]
        :param output_dir:     directory to output edges and new graph [data/edges/]
        :param train_fraction: fraction of edges to emit as training
        :param validation:     should we make validation edges? [False]
        :param seed:    random seed [42]
    Returns:
        None.
    """
    logging.basicConfig(level=logging.INFO)
    logging.info("Loading graph from nodes %s and edges %s files" % (nodes, edges))
    graph = Graph.from_csv(
        default_edge_type="biolink:Association",
        default_node_type="biolink:NamedThing",
        destinations_column="object",
        directed=False,
        edge_list_header=True,
        edge_list_separator="\t",
        edge_path=edges,
        edge_list_edge_types_column="predicate",
        node_list_header=True,
        node_list_node_types_column="category",
        node_list_separator="\t",
        node_path=nodes,
        nodes_column="id",
        sources_column="subject",
    )

    os.makedirs(output_dir, exist_ok=True)

    # make positive edges
    logging.info("Making positive edges")
    pos_train_edges, pos_test_edges = graph.random_holdout(
        random_state=seed, train_size=train_fraction
    )
    if validation:
        pos_valid_edges, pos_test_edges = pos_test_edges.random_holdout(
            random_state=seed, train_size=0.5
        )

    # make negative edges
    logging.info("Making negative edges")

    all_negative_edges = pos_train_edges.sample_negative_graph(
        random_state=seed, number_of_negative_samples=graph.get_number_of_edges()
    )
    neg_train_edges, neg_test_edges = all_negative_edges.random_holdout(
        random_state=seed, train_size=train_fraction
    )
    if validation:
        neg_test_edges, neg_valid_edges = neg_test_edges.random_holdout(
            random_state=seed, train_size=0.5
        )

    #
    # write out positive edges
    #
    # training:
    logging.info("Writing out positive edges")
    pos_train_edges_outfile = os.path.join(output_dir, "pos_train_edges.tsv")
    pos_train_nodes_outfile = os.path.join(output_dir, "pos_train_nodes.tsv")
    pos_test_edges_outfile = os.path.join(output_dir, "pos_test_edges.tsv")
    pos_valid_edges_outfile = os.path.join(output_dir, "pos_valid_edges.tsv")

    pos_train_edges.dump_edges(path=pos_train_edges_outfile)
    pos_train_edges.dump_nodes(path=pos_train_nodes_outfile)
    pos_test_edges.dump_edges(path=pos_test_edges_outfile)
    if validation:
        pos_valid_edges.dump_edges(path=pos_valid_edges_outfile)

    #
    # write out negative edges
    #
    logging.info("Writing out negative edges")
    neg_train_edges_outfile = os.path.join(output_dir, "neg_train_edges.tsv")
    neg_test_edges_outfile = os.path.join(output_dir, "neg_test_edges.tsv")
    neg_valid_edges_outfile = os.path.join(output_dir, "neg_valid_edges.tsv")

    neg_train_edges.dump_edges(path=neg_train_edges_outfile)
    neg_test_edges.dump_edges(path=neg_test_edges_outfile)
    if validation:
        neg_valid_edges.dump_edges(path=neg_valid_edges_outfile)


def df_to_tsv(df: pd.DataFrame, outfile: str, sep="\t", index=False) -> None:
    """Convert data frame to CSV, and usually a TSV."""
    df.to_csv(outfile, sep=sep, index=index)


def make_negative_edges(
    nodes_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    edge_label: str = "negative_edge",
    relation: str = "negative_edge",
) -> pd.DataFrame:
    """
    Produce negative holdout set.

    Given a graph (as nodes and edges pandas dataframes),
    select num_edges holdouts that are NOT present in the graph.
    :param nodes_df: pandas dataframe containing node info
    :param edges_df: pandas dataframe containing edge info
    :param relation: string to put in relation column
    :param edge_label: string to put in edge_label column
    :return:
    """
    if "subject" not in list(edges_df.columns) or "object" not in list(
        edges_df.columns
    ):
        raise ValueError("Can't find subject or object column in edges")

    if "id" not in list(nodes_df.columns):
        raise ValueError("Can't find id column in nodes")

    edge_list = _generate_negative_edges(
        nodes_df=nodes_df, edges_df=edges_df, edge_label=edge_label, relation=relation
    )
    return edge_list


def _generate_negative_edges(
    nodes_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    edge_label: str,
    relation: str,
    rseed: Optional[str] = None,
) -> pd.DataFrame:
    if rseed:
        logging.debug("Setting random seed")
        random.seed(rseed)

    with tqdm(total=8) as pbar:
        unique_nodes = list(
            np.unique(np.concatenate((nodes_df.id, edges_df.subject, edges_df.object)))
        )
        pbar.update()

        pbar.set_description("Making random pairs of nodes")
        random_subjects = [
            unique_nodes[random.randint(0, len(unique_nodes) - 1)]
            for _ in range(2 * edges_df.shape[0])
        ]
        random_objects = [
            unique_nodes[random.randint(0, len(unique_nodes) - 1)]
            for _ in range(2 * edges_df.shape[0])
        ]
        possible_edges = pd.DataFrame(
            {"subject": random_subjects, "object": random_objects}
        )
        pbar.update()

        pbar.set_description("Eliminating duplicated negative edges")
        possible_edges.drop_duplicates(
            subset=["subject", "object"], keep=False, inplace=True
        )
        pbar.update()

        pbar.set_description("Eliminating positives edges")
        negative_edges = possible_edges.merge(
            edges_df.drop_duplicates(),
            on=["subject", "object"],
            how="left",
            indicator=True,
        )
        negative_edges = negative_edges[negative_edges["_merge"] == "left_only"]
        pbar.update()

        pbar.set_description("Dropping reflexive edges")
        negative_edges = negative_edges[
            negative_edges["subject"] != negative_edges["object"]
        ]
        pbar.update()

        pbar.set_description("Selecting %i edges..." % edges_df.shape[0])
        # theoretically might not have enough edges here
        if negative_edges.shape[0] < edges_df.shape[0]:
            warnings.warn(
                "Couldn't generate %i negative edges - only %i edges left "
                "after removing positives and reflexives"
                % (edges_df.shape[0], negative_edges.shape[0])
            )
            negative_edges = negative_edges.head(negative_edges.shape[0])
        else:
            # select only num_edges edges
            negative_edges = negative_edges.head(edges_df.shape[0])
        pbar.update()

        # only subject and object
        pbar.set_description("Making new dataframe")
        negative_edges = negative_edges[["subject", "object"]]
        pbar.update()

        # add edge_label and relation
        negative_edges = pd.DataFrame(
            {
                "subject": negative_edges["subject"],
                "predicate": edge_label,
                "object": negative_edges["object"],
                "relation": relation,
            }
        )
        pbar.update()
        pbar.set_description("Done making negative edges")

    return negative_edges


def make_positive_edges(
    nodes_df: pd.DataFrame, edges_df: pd.DataFrame, train_fraction: float
) -> List[pd.DataFrame]:
    """
    Produce holdout set of positive edges.

    Positive edges are randomly selected from the edges in the graph, IFF both nodes
    participating in the edge have a degree greater than min_degree (to avoid creating
    disconnected components). This edge is then removed in the output graph. Negative
    edges are selected by randomly selecting pairs of nodes that are not connected by an
    edge.
    :param nodes_df: pandas dataframe with node info, generated from KGX TSV file
    :param edges_df: pandas dataframe with edge info, generated from KGX TSV file
    :param train_fraction: fraction of input edges to emit as test (and optionally
                  validation) edges
    :return:  pandas dataframes:
    training_edges_df: a dataframe with training edges with positive edges we
                    selected for test removed from graph
    test_edges_df: a dataframe with test positive edges
    """
    if "subject" not in list(edges_df.columns) or "object" not in list(
        edges_df.columns
    ):
        raise ValueError("Can't find subject or object column in edges")

    if "id" not in list(nodes_df.columns):
        raise ValueError("Can't find id column in nodes")

    with tqdm(total=7) as pbar:
        pbar.set_description("Copying edges")
        test_edges = edges_df.copy(deep=True)
        pbar.update()

        # count degrees
        pbar.set_description("Calculating degrees")
        subj_degree = edges_df["subject"].value_counts()
        subj_degree_df = pd.DataFrame(
            {
                "subject": list(subj_degree.index),
                "subj_degree": list(subj_degree.values),
            }
        )
        obj_degree = edges_df["object"].value_counts()
        obj_degree_df = pd.DataFrame(
            {"object": list(obj_degree.index), "obj_degree": list(obj_degree.values)}
        )
        pbar.update()

        pbar.set_description("Merging degrees")
        test_edges = test_edges.merge(subj_degree_df, how="left", on="subject")
        test_edges = test_edges.merge(obj_degree_df, how="left", on="object")
        pbar.update()

        pbar.set_description("Adding edge_label and relation columns")
        test_edges = test_edges.sample(frac=(1 - train_fraction))
        test_edges["predicate"] = "positive_edge"
        test_edges["relation"] = "positive_edge"
        pbar.update()

        pbar.set_description("Making training edges")
        train_edges = edges_df.copy(deep=True)
        pbar.update()

        pbar.set_description("Removing test edges from training data")
        train_edges.drop(train_edges.index[test_edges.index], inplace=True)
        pbar.update()
        pbar.set_description("Done making positive edges")

    return [train_edges, test_edges]


def tsv_to_df(tsv_file: str, *args, **kwargs) -> pd.DataFrame:
    """Read in a TSV file and return a pandas dataframe.

    :param tsv_file: file to read in
    :return: pandas dataframe
    """
    df = pd.read_csv(tsv_file, sep="\t", *args, **kwargs)
    return df
