#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from typing import List, Union

import click
from kg_covid_19 import download as kg_download
from kg_covid_19 import transform as kg_transform
from kg_covid_19.edges import make_edges
from kg_covid_19.load_utils.merge_kg import load_and_merge
from kg_covid_19.query import QUERIES, run_query
from kg_covid_19.transform import DATA_SOURCES


@click.group()
def cli():
    pass


@cli.command()
@click.option("yaml_file", "-y", required=True, default="download.yaml",
              type=click.Path(exists=True))
@click.option("output_dir", "-o", required=True, default="data/raw")
@click.option("ignore_cache", "-i", is_flag=True, default=False,
              help='ignore cache and download files even if they exist [false]')
def download(*args, **kwargs) -> None:
    """Downloads data files from list of URLs (default: download.yaml) into data
    directory (default: data/raw).

    Args:
        yaml_file: Specify the YAML file containing a list of datasets to download.
        output_dir: A string pointing to the directory to download data to.
        ignore_cache: If specified, will ignore existing files and download again.

    Returns:
        None.

    """

    kg_download(*args, **kwargs)

    return None


@cli.command()
@click.option("input_dir", "-i", default="data/raw", type=click.Path(exists=True))
@click.option("output_dir", "-o", default="data/transformed")
@click.option("sources", "-s", default=None, multiple=True,
              type=click.Choice(DATA_SOURCES.keys()))
def transform(*args, **kwargs) -> None:
    """Calls scripts in kg_covid_19/transform/[source name]/ to transform each source
    into nodes and edges.

    Args:
        input_dir: A string pointing to the directory to import data from.
        output_dir: A string pointing to the directory to output data to.
        sources: A list of sources to transform.

    Returns:
        None.

    """

    # call transform script for each source
    kg_transform(*args, **kwargs)

    return None


@cli.command()
@click.option('yaml', '-y', default="merge.yaml", type=click.Path(exists=True))
def load(yaml: str) -> None:
    """Use KGX to load subgraphs to create a merged graph.

    Args:
        yaml: A string pointing to a KGX compatible config YAML.

    Returns:
        None.

    """

    load_and_merge(yaml)


@cli.command()
@click.option("query", "-q", required=True, default=None, multiple=False,
              type=click.Choice(QUERIES.keys()))
@click.option("input_dir", "-i", default="data/")
@click.option("output_dir", "-o", default="data/queries/")
def query(query: str, input_dir: str, output_dir: str) -> None:
    """Perform a query of knowledge graph using a class contained in query_utils

    Args:
        query: A query class containing instructions for performing a query
        input_dir: Directory where any input files required to execute query are
            located (typically 'data', where transformed and merged graph files are)
        output_dir: Directory to output results of query

    Returns:
        None.

    """
    run_query(query=query, input_dir=input_dir, output_dir=output_dir)


@cli.command()
@click.option("nodes", "-n", default="data/merged/nodes.tsv", type=click.Path(exists=True))
@click.option("edges", "-e", default="data/merged/edges.tsv", type=click.Path(exists=True))
@click.option("output_dir", "-o", default="data/edges/", type=click.Path())
@click.option("train_fraction", "-t", default=0.8, type=float)
@click.option("validation", "-v", is_flag=True, default=False)
@click.option("min_degree", "-m", default=2, type=click.IntRange(min=0, max=None,
                                                                 clamp=False))
def edges(*args, **kwargs) -> None:
    """Make sets of edges for ML training

    Given a graph (from formatted node and edge TSVs), output positive edges and negative
    edges for use in machine learning.

    To generate positive edges: a set of test positive edges equal in number to
    [(1 - train_fraction) * number of edges in input graph] are randomly selected from
    the edges in the input graph, such that both nodes participating in the edge have a
    degree greater than min_degree (to avoid creating disconnected components). These
    edges are emitting as positive test edges. (If -v == true, the test positive edges
    are divided equally to yield test and validation positive edges.) These edges are
    then removed from the edges of the input graph, and these are emitted as the
    training edges.

    Negative edges are selected by randomly selecting pairs of nodes that are not
    connected by an edge in the input graph. The number of negative edges emitted is
    equal to the number of positive edges emitted above.

    Outputs these files in [output_dir]:
        pos_train_edges.tsv - positive edges for training (this is the input graph with
                      test [and validation] positive edges removed)
        pos_test_edges.tsv - positive edges for testing
        pos_valid_edges.tsv (optional) - positive edges for validation
        neg_train.tsv - a set of edges not present in input graph for training
        neg_test.tsv - a set of edges not present in input graph for testing
        neg_valid.tsv (optional) - a set of edges not present in input graph for
                      validation

    Args:
        :param nodes:   nodes for input graph, in KGX TSV format [data/merged/nodes.tsv]
        :param edges:   edges for input graph, in KGX TSV format [data/merged/edges.tsv]
        :param output_dir:     directory to output edges and new graph [data/edges/]
        :param train_fraction: fraction of edges to emit as training [0.8]
        :param validation:     should we make validation edges? [False]
        :param min_degree      when choosing edges, what is the minimum degree of nodes
                        involved in the edge [1]
    """
    make_edges(*args, **kwargs)


if __name__ == "__main__":
    cli()
