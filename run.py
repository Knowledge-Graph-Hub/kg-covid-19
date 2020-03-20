import os
from os import path

import click
import urllib.request


@click.group()
def cli():
    pass


@cli.command()
@click.option("input_file", "-i", required=True, default="incoming.txt",
              type=click.Path(exists=True))
@click.option("output_dir", "-o", required=True, default="data/raw")
@click.option("overwrite", "-w", default=True)
def download(input_file, output_dir, overwrite):
    """
    download data files from list of URLs (default: incoming.txt) into data directory
    (default: data/)
    """
    urls = []

    if not path.exists(output_dir):
        os.mkdir(output_dir)
    with open(input_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)

    for url in urls:
        outfile = os.path.join(output_dir, url.split("/")[-1])
        if path.exists(outfile):
            os.remove(outfile)
        urllib.request.urlretrieve(url, filename=os.path.join(outfile))


@cli.command()
@click.option("input_dir", "-i", default="data/raw", type=click.Path(exists=True))
@click.option("output_dir", "-o", default="data/transformed")
def transform(input_dir, output_dir):
    """
    ingest files in data/raw, transform them into networkx graphs, output them in
    data/transformed
    """

    # call transform script for each source


if __name__ == "__main__":
    cli()

