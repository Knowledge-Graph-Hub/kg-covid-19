#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import click
from kg_covid_19 import download as kg_download
from kg_covid_19 import transform as kg_transform
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
@click.option("input_dir", "-i", default="data/merged/", type=click.Path(exists=True))
@click.option("output_dir", "-o", default="data/edges/")
def edges(input_dir: str, output_dir: str) -> None:
    """Make positive and negative edges for ML training

    Args:
        input_dir: A string pointing to the directory to import data from.
        output_dir: A string pointing to the directory to output data to.
    """
    pass


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


if __name__ == "__main__":
    cli()
