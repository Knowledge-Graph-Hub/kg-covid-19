#!/usr/bin/env python
# -*- coding: utf-8 -*-


import gzip
import logging
import os

from typing import Dict, List

from kg_covid_19.transform_utils.transform import Transform
from kg_covid_19.utils.transform_utils import write_node_edge_item, \
    get_item_by_priority, ItemInDictNotFound

"""
Ingest drug - drug target interactions from Drug Central

Essentially just ingests and transforms this file:
http://unmtid-shinyapps.net/download/drug.target.interaction.tsv.gz

And extracts Drug -> Gene interactions
"""


class DrugCentralTransform(Transform):

    def __init__(self) -> None:
        super().__init__(source_name="drug_central")  # set some variables

    def run(self) -> None:
        """Method is called and performs needed transformations to process the Drug Central data, additional information
     on this data can be found in the comment at the top of this script"""

        interactions_file = os.path.join(self.input_base_dir, "drug.target.interaction.tsv.gz")
        os.makedirs(self.output_dir, exist_ok=True)
        drug_node_type = "biolink:Drug"
        gene_node_type = "biolink:Gene"
        drug_gene_edge_label = "biolink:interacts_with"
        drug_gene_edge_relation = "RO:0002436"  # molecularly interacts with
        self.edge_header = ['subject', 'edge_label', 'object', 'relation', 'comment']

        with open(self.output_node_file, 'w') as node, \
                open(self.output_edge_file, 'w') as edge, \
                gzip.open(interactions_file, 'rt') as interactions:

            node.write("\t".join(self.node_header) + "\n")
            edge.write("\t".join(self.edge_header) + "\n")

            header_items = parse_header(interactions.readline())

            for line in interactions:
                items_dict = parse_drug_central_line(line, header_items)

                # get gene ID
                try:
                    gene_id = get_item_by_priority(items_dict, ['ACCESSION'])
                except ItemInDictNotFound:
                    # lines with no ACCESSION entry only contain drug info, no target
                    # info - not ingesting these
                    logging.info(
                        "No gene information for this line:\n{}\nskipping".format(line))
                    continue

                # get drug ID
                drug_id = get_item_by_priority(items_dict,
                                               ['ACT_SOURCE_URL',
                                                'MOA_SOURCE_URL',
                                                'DRUG_NAME'])

                # WRITE NODES
                # drug - ['id', 'name', 'category']
                write_node_edge_item(fh=node,
                                     header=self.node_header,
                                     data=[drug_id,
                                           items_dict['DRUG_NAME'],
                                           drug_node_type])

                write_node_edge_item(fh=node,
                                     header=self.node_header,
                                     data=[gene_id,
                                           items_dict['GENE'],
                                           gene_node_type])

                # WRITE EDGES
                # ['subject', 'edge_label', 'object', 'relation', 'comment']
                write_node_edge_item(fh=edge,
                                     header=self.edge_header,
                                     data=[drug_id,
                                           drug_gene_edge_label,
                                           gene_id,
                                           drug_gene_edge_relation,
                                           items_dict['ACT_COMMENT']])

        return None


def parse_drug_central_line(this_line: str, header_items: List) -> Dict:
    """Methods processes a line of text from Drug Central.

    Args:
        this_line: A string containing a line of text.
        header_items: A list of header items.

    Returns:
        item_dict: A dictionary of header items and a processed Drug Central string.
    """

    items = this_line.strip().split("\t")
    item_dict = dict(zip(header_items, items))

    return item_dict


def parse_header(header_string: str, sep: str = '\t') -> List:
    """Parses header data.

    Args:
        header_string: A string containing header items.
        sep: A string containing a delimiter.

    Returns:
        A list of header items.
    """

    header = header_string.strip().split(sep)

    return [i.replace('"', '') for i in header]
