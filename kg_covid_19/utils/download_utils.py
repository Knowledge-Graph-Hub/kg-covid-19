#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import os
from urllib.request import Request, urlopen

import yaml
from os import path
from tqdm.auto import tqdm  # type: ignore

def download_from_yaml(yaml_file: str, output_dir: str,
                       ignore_cache: bool = False) -> None:
    """Given an download info from an download.yaml file, download all files

    Args:
        yaml_file: A string pointing to the download.yaml file, to be parsed for things to download.
        output_dir: A string pointing to where to write out downloaded files.
        ignore_cache: Ignore cache and download files even if they exist [false]

    Returns:
        None.
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
            logging.info("Retrieving %s from %s" % (outfile, item['url']))

            if path.exists(outfile):
                if ignore_cache:
                    logging.info("Deleting cached version of {}".format(outfile))
                    os.remove(outfile)
                else:
                    logging.info("Using cached version of {}".format(outfile))
                    continue

            req = Request(item['url'], headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req) as response, open(outfile, 'wb') as out_file:  # type: ignore
                    data = response.read()  # a `bytes` object
                    out_file.write(data)

    return None
