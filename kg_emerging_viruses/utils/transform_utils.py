import logging
from typing import List, Union


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
                logging.warning("Unexpected number of rows in {}", row)
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


def write_node_edge_item(fh,
                         header: list,
                         data: list,
                         sep: str = '\t') -> None:
    """Write out a single line for a node or an edge in *.tsv
    :param fh: file handle of node or edge file
    :param header: list of header items
    :param data: data for line to write out
    :param sep: separator [\t]
    :return:
    """
    if len(header) != len(data):
        raise Exception("header and data are not the same length")
    try:
        fh.write(sep.join(data) + "\n")
    except:
        foo = 1


def get_item_by_priority(items_dict: dict, keys_by_priority: list) -> Union[str, None]:
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
        foo = 1
    return value
