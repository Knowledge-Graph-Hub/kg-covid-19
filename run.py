#!/usr/bin/env python
# -*- coding: utf-8 -*-


import click
from kg_emerging_viruses import download as kg_download
from kg_emerging_viruses import transform as kg_transform


@click.group()
def cli():
    pass


@cli.command()
@click.option("yaml_file", "-y", required=True, default="download.yaml", type=click.Path(exists=True))
@click.option("output_dir", "-o", required=True, default="data/raw")
def download(*args, **kwargs) -> None:
    """Downloads data files from list of URLs (default: download.yaml) into data directory (default: data/).

    Returns:
        None.
    """

    kg_download(*args, **kwargs)

    return None


@cli.command()
@click.option("input_dir", "-i", default="data/raw", type=click.Path(exists=True))
@click.option("output_dir", "-o", default="data/transformed")
def transform(*args, **kwargs) -> None:
    """Calls scripts in kg_emerging_viruses/transform/[source name]/ to transform each source into a graph format that
    KGX can ingest directly, in either TSV or JSON format:
    https://github.com/NCATS-Tangerine/kgx/blob/master/data-preparation.md

    Returns:
        None.
    """

    # call transform script for each source
    kg_transform(*args, **kwargs)

    return None


if __name__ == "__main__":
    cli()
