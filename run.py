import click

from kg_emerging_viruses.transform.zhou_host_proteins import zhou_transform
from kg_emerging_viruses.utils.download_utils import download_from_yaml


@click.group()
def cli():
    pass


@cli.command()
@click.option("yaml_file", "-y", required=True, default="download.yaml",
              type=click.Path(exists=True))
@click.option("output_dir", "-o", required=True, default="data/raw")
def download(yaml_file, output_dir):
    """
    download data files from list of URLs (default: download.yaml) into data directory
    (default: data/)
    """

    download_from_yaml(yaml_file=yaml_file, output_dir=output_dir)


@cli.command()
@click.option("input_dir", "-i", default="data/raw", type=click.Path(exists=True))
@click.option("output_dir", "-o", default="data/transformed")
def transform(input_dir, output_dir):
    """
    Call scripts in kg_emerging_viruses/transform/[source name]/
    to transform each source into a graph format that KGX can
    ingest directly, in either TSV or JSON format:
    https://github.com/NCATS-Tangerine/kgx/blob/master/data-preparation.md
    """

    # call transform script for each source
    zhou_transform.run()


if __name__ == "__main__":
    cli()
