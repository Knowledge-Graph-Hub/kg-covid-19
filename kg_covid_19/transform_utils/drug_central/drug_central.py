#!/usr/bin/env python
# -*- coding: utf-8 -*-


import gzip
import os

from typing import Dict, List

from kg_emerging_viruses.transform_utils.transform import Transform
from kg_emerging_viruses.utils.transform_utils import write_node_edge_item, get_item_by_priority

"""
Ingest drug - drug target interactions from Drug Central
https://www.nature.com/articles/s41421-020-0153-3

GitHub Issue: https://github.com/kg-emerging-viruses/kg-emerging-viruses/issues/5


Write node and edge headers that look something like:

Node: 
id  name    category
gene:1234   TBX4    Gene 

Edge: 
subject edge_label  object   relation
gene:1234  contributes_to_condition    MONDO:0005002   RO:0003304
"""


class DrugCentralTransform(Transform):

    def __init__(self) -> None:
        super().__init__(source_name="drug_central")  # set some variables

    def run(self) -> None:
        """Method is called and performs needed transformations to process the Drug Central data, additional information
     on this data can be found in the comment at the top of this script"""

        interactions_file = os.path.join(self.input_base_dir, "drug.target.interaction.tsv.gz")
        os.makedirs(self.output_dir, exist_ok=True)
        drug_node_type = "Drug"
        gene_node_type = "Gene"
        drug_gene_edge_label = "affects"
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
                gene_id = get_item_by_priority(items_dict, ['ACCESSION'])

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

                # gene - ['id', 'name', 'category']
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
                                           drug_gene_edge_label,
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
