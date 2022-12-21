"""Download utilities."""

import json
import logging
import os
from os import path
from urllib.request import Request, urlopen

import compress_json  # type: ignore
import elasticsearch
import elasticsearch.helpers
import yaml
from tqdm.auto import tqdm  # type: ignore


def download_from_yaml(
    yaml_file: str, output_dir: str, ignore_cache: bool = False
) -> None:
    """
    Download files specified in an input yaml.

    Given an download info from an download.yaml file,
    download all files.
    Args:
        yaml_file: A string pointing to the
        download.yaml file, to be parsed for things
        to download.
        output_dir: A string pointing to where to write
        out downloaded files.
        ignore_cache: Ignore cache and download files
        even if they exist [false]
    Returns:
        None.
    """
    os.makedirs(output_dir, exist_ok=True)
    with open(yaml_file) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        for item in tqdm(data, desc="Downloading files"):
            if "url" not in item:
                logging.warning("Couldn't find url for source in {}".format(item))
                continue
            outfile = os.path.join(
                output_dir,
                item["local_name"]
                if "local_name" in item
                else item["url"].split("/")[-1],
            )
            logging.info("Retrieving %s from %s" % (outfile, item["url"]))

            if path.exists(outfile):
                if ignore_cache:
                    logging.info("Deleting cached version of {}".format(outfile))
                    os.remove(outfile)
                else:
                    logging.info("Using cached version of {}".format(outfile))
                    continue

            if "api" in item:
                download_from_api(item, outfile)
            else:
                req = Request(item["url"], headers={"User-Agent": "Mozilla/5.0"})
                with urlopen(req) as response, open(outfile, "wb") as out_file:
                    data = response.read()  # a `bytes` object
                    out_file.write(data)

    return None


def download_from_api(yaml_item, outfile) -> None:
    """
    Download from an Elasticsearch API.

    Args:
        yaml_item: item to be download, parsed from yaml
        outfile: where to write out file
    Returns:
    """
    if yaml_item["api"] == "elasticsearch":
        es_conn = elasticsearch.Elasticsearch(hosts=[yaml_item["url"]])
        query_data = compress_json.local_load(
            os.path.join(os.getcwd(), yaml_item["query_file"])
        )
        output = open(outfile, "w")
        records = elastic_search_query(
            es_conn, index=yaml_item["index"], query=query_data
        )
        json.dump(records, output)
        return None
    else:
        raise RuntimeError(f"API {yaml_item['api']} not supported")


def elastic_search_query(
    es_connection,
    index,
    query,
    scroll: str = "1m",
    request_timeout: int = 60,
    preserve_order: bool = True,
):
    """
    Fetch records from the given URL and query parameters.

    Args:
        es_connection: elastic search connection
        index: the elastic search index for query
        query: query
        scroll: scroll parameter passed to elastic search
        request_timeout: timeout parameter passed to elastic search
        preserve_order: preserve order param passed to elastic search
    Returns:
        All records for query
    """
    records = []
    results = elasticsearch.helpers.scan(
        client=es_connection,
        index=index,
        scroll=scroll,
        request_timeout=request_timeout,
        preserve_order=preserve_order,
        query=query,
    )

    for item in tqdm(results, desc="querying for index: " + index):
        records.append(item)

    return records
