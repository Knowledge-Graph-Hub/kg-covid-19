import click
from kg_emerging_viruses import transform as kg_transform, download as kg_download


@click.group()
def cli():
    pass


@cli.command()
@click.option("yaml_file", "-f", required=True, default="download.yaml",
              type=click.Path(exists=True))
@click.option("output_dir", "-o", required=True, default="data/raw")
def download(*args, **kwargs):
    """
    download data files from list of URLs (default: download.yaml) into data directory
    (default: data/)
    """

    kg_download(*args, **kwargs)


@cli.command()
@click.option("input_dir", "-i", default="data/raw", type=click.Path(exists=True))
@click.option("output_dir", "-o", default="data/transformed")
def transform(*args, **kwargs):
    """
    Call scripts in kg_emerging_viruses/transform/[source name]/
    to transform each source into a graph format that KGX can
    ingest directly, in either TSV or JSON format:
    https://github.com/NCATS-Tangerine/kgx/blob/master/data-preparation.md
    """

    # call transform script for each source
    kg_transform(*args, **kwargs)


if __name__ == "__main__":
    cli()
