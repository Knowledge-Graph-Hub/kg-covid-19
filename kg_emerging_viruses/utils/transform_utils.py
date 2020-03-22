import logging
from typing import List


def multi_page_table_to_list(multi_page_table) -> List[dict]:
    """
    method to turn table data returned from tabula.io.read_pdf(),
    possibly broken over several pages, into a list of dicts,
    one dict for each row
    :param multi_page_table:
    :return: list of dicts, where each dict is item from one row
    """

    # iterate through data for each of 3 pages
    table_data = []  # list of dicts

    header_items = get_header_items(multi_page_table[0])

    for this_page in multi_page_table:
        for row in this_page['data']:
            if len(row) != 4:
                logging.warning("Unexpected number of rows in {}".format(row))
            items = [d['text'] for d in row]
            this_dict = dict(zip(header_items, items))
            table_data.append(this_dict)
    return table_data


def get_header_items(table_data) -> list:
    """
    utility fxn to get header from (first page of) a table
    :param table_data: data, as list of dicts from tabula.io.read_pdf()
    :return: array of header items
    """
    header = table_data['data'].pop(0)
    header_items = [d['text'] for d in header]
    return header_items


def write_node_edge_item(fh, header: list, data: list, sep: str ='\t') -> None:
    if len(header) != len(data):
        raise Exception("header and data are not the same length")
    fh.write(sep.join(data) + "\n")

