#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging

from typing import Any, Dict, List


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
    """Method

    """

    if len(header) != len(data):
        raise Exception('Header and data are not the same length.')
    else:
        fh.write(sep.join(data) + "\n")

    return None
