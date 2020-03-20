import os
from os import path

import click
from encodeproject import download
from tqdm.auto import tqdm
from tabula import io

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
    os.makedirs(output_dir, exist_ok=True)
    with open(input_file) as f:
        urls = [
            url
            for url in f
            if url and not url.startswith("#")
        ]

    for url in tqdm(urls, desc="Downloading files"):
        outfile = os.path.join(output_dir, url.split("/")[-1])
        if path.exists(outfile):
            os.remove(outfile)
        download(
            url=url,
            path=outfile
        )


@cli.command()
@click.option("input_dir", "-i", default="data/raw", type=click.Path(exists=True))
@click.option("output_dir", "-o", default="data/transformed")
def transform(input_dir, output_dir):
    """
    ingest files in data/raw, transform them into networkx graphs, output them in
    data/transformed
    """
    pass


if __name__ == "__main__":
    cli()
