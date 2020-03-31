#!/usr/bin/env python
# -*- coding: utf-8 -*-
import gzip
import logging
from typing import Any, Dict, List, Union
from tqdm import tqdm  # type: ignore


class TransformError(Exception):
    """Base class for other exceptions"""
    pass


class ItemInDictNotFound(TransformError):
    """Raised when the input value is too small"""
    pass


# TODO: option to further refine typing of method arguments below.

def multi_page_table_to_list(multi_page_table: Any) -> List[Dict]:
    """Method to turn table data returned from tabula.io.read_pdf(), possibly broken over several pages, into a list
    of dicts, one dict for each row.

    Args:
        multi_page_table:

    Returns:
        table_data: A list of dicts, where each dict is item from one row.
    """

    # iterate through data for each of 3 pages
    table_data: List[Dict] = []

    header_items = get_header_items(multi_page_table[0])

    for this_page in multi_page_table:
        for row in this_page['data']:
            if len(row) != 4:
                logging.warning('Unexpected number of rows in {}'.format(row))

            items = [d['text'] for d in row]
            this_dict = dict(zip(header_items, items))
            table_data.append(this_dict)

    return table_data


def get_header_items(table_data: Any) -> List:
    """Utility fxn to get header from (first page of) a table.

    Args:
        table_data: Data, as list of dicts from tabula.io.read_pdf().

    Returns:
        header_items: An array of header items.
    """

    header = table_data['data'].pop(0)
    header_items = [d['text'] for d in header]

    return header_items


def write_node_edge_item(fh: Any, header: List, data: List, sep: str = '\t') -> None:
    """Write out a single line for a node or an edge in *.tsv
    :param fh: file handle of node or edge file
    :param header: list of header items
    :param data: data for line to write out
    :param sep: separator [\t]
    :return:
    """
    if len(header) != len(data):
        raise Exception('Header and data are not the same length.')
    else:
        try:
            fh.write(sep.join(data) + "\n")
        except:
            logging.warning("Can't write data for {}".format(data))

    return None


def get_item_by_priority(items_dict: dict, keys_by_priority: list) -> str:
    """Retrieve item from a dict using a list of keys, in descending order of priority

    :param items_dict:
    :param keys_by_priority: list of keys to use to find values
    :return: str: first value in dict for first item in keys_by_priority
    that isn't blank, or None
    """
    value = None
    for key in keys_by_priority:
        if key in items_dict and items_dict[key] != '':
            value = items_dict[key]
            break
    if value is None:
        logging.warning("Can't find item in items_dict {}".format(items_dict))
        raise ItemInDictNotFound("Can't find item in items_dict {}".format(items_dict))
    return value


def uniprot_make_name_to_id_mapping(dat_gz_file: str) -> dict:
    """Given a Uniprot dat.gz file, like this:
    ftp://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/idmapping/by_organism/HUMAN_9606_idmapping.dat.gz
     makes dict with name to id mapping
    
    :param dat_gz_file: 
    :return: dict with mapping
    """""
    name_to_id_map = dict()
    logging.info("Making uniprot name to id map")
    with gzip.open(dat_gz_file, mode='rb') as file:
        for line in tqdm(file):
            items = line.decode().strip().split('\t')
            name_to_id_map[items[2]] = items[0]
    return name_to_id_map


def uniprot_name_to_id(name_to_id_map: dict, name: str) -> Union[str, None]:
    """Uniprot name to ID mapping

    :param name_to_id_map: mapping dict[name] -> id
    :param name: name
    :return: id string, or None
    """
    if name in name_to_id_map:
        return name_to_id_map[name]
    else:
        return None
