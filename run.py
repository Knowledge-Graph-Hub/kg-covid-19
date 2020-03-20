import os

import yaml
from os import path
import click
from encodeproject import download as encode_download
from tqdm.auto import tqdm

@click.group()
def cli():
    pass


@cli.command()
@click.option("incoming", "-i", required=True, default="incoming.yaml",
              type=click.Path(exists=True))
@click.option("output_dir", "-o", required=True, default="data/raw")
@click.option("overwrite", "-w", default=True)
def download(incoming, output_dir, overwrite):
    """
    download data files from list of URLs (default: incoming.yaml) into data directory
    (default: data/)
    """

    urls = []
    os.makedirs(output_dir, exist_ok=True)
    with open(incoming) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        for source in data['sources']:
            if 'url' not in source:
                raise Exception("Couldn't find url for source in {}", source)
            urls.append(source['url'])

    for this_url in tqdm(urls, desc="Downloading files"):
        outfile = os.path.join(output_dir, this_url.split("/")[-1])
        if path.exists(outfile):
            os.remove(outfile)
        encode_download(
            url=this_url,
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

    # call transform script for each source


if __name__ == "__main__":
    cli()
