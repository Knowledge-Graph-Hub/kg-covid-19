import os

import click
import wget


@click.group()
def cli():
    pass


@cli.command()
@click.option("input_file", "-i", default="incoming.txt", type=click.Path(exists=True))
@click.option("output_dir", "-o", default="data", type=click.Path(exists=True))
def download(input_file, output_dir):
    """
    download data files from list of URLs (default: incoming.txt) into data directory
    (default: data/)
    """
    urls = []
    with open(input_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)

    for url in urls:
        wget.download(url, out=os.path.join(output_dir,
                                            url.split("/")[-1]))


@cli.command()
@click.option("input_dir", "-i", default="data/raw", type=click.Path(exists=True))
@click.option("output_dir", "-o", default="data/transformed")
def transform(input_dir, output_dir):
    """
    ingest files in data/raw, transform them into networkx graphs, output them in
    data/transformed
    """
    with open(input_dir) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)

    os.makedirs(output_dir)

    for url in urls:
        wget.download(url, out=os.path.join(output_dir,
                                            url.split("/")[-1]))


if __name__ == "__main__":
    cli()

