import logging
import os
from encodeproject import download as encode_download
from tqdm.auto import tqdm

import yaml
from os import path


def download_from_yaml(yaml_file: str, output_dir: str) -> None:
    """Given an download info from an download.yaml file, download all files

    :param yaml_file: download.yaml file, to be parsed for things to download
    :param output_dir: where to write out downloaded files
    :return:
    """

    os.makedirs(output_dir, exist_ok=True)
    with open(yaml_file) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        for item in tqdm(data, desc="Downloading files"):
            if 'url' not in item:
                logging.warning("Couldn't find url for source in {}".format(item))
                continue
            outfile = os.path.join(
                output_dir,
                item['local_name']
                if 'local_name' in item
                else item['url'].split("/")[-1]
            )

            if path.exists(outfile):
                os.remove(outfile)

            encode_download(url=item['url'], path=outfile)
