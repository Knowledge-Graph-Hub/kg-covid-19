#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import gzip
import logging
import os
import re
import tempfile
from collections import defaultdict

from typing import Dict, List, Optional

from kg_covid_19.transform_utils.transform import Transform
from kg_covid_19.utils.transform_utils import write_node_edge_item, \
    get_item_by_priority, ItemInDictNotFound, parse_header, data_to_dict, \
    unzip_to_tempdir

"""
Ingest drug - drug target interactions from Drug Central

Essentially just ingests and transforms this file:
http://unmtid-shinyapps.net/download/drug.target.interaction.tsv.gz

And extracts Drug -> Protein interactions
"""


class DrugCentralTransform(Transform):

    def __init__(self, input_dir: str = None, output_dir: str = None) -> None:
        source_name = "drug_central"
        super().__init__(source_name, input_dir, output_dir)  # set some variables
        self.node_header = ['id', 'name', 'category', 'TDL', 'provided_by']

    def run(self, data_file: Optional[str] = None, species: str = "Homo sapiens") -> None:
        """Method is called and performs needed transformations to process the Drug
        Central data, additional information
        on this data can be found in the comment at the top of this script"""

        interactions_file = os.path.join(self.input_base_dir,
                                         "drug.target.interaction.tsv.gz")
        os.makedirs(self.output_dir, exist_ok=True)
        drug_node_type = "biolink:Drug"
        uniprot_curie_prefix = "UniProtKB:"
        drug_curie_prefix = "DrugCentral:"
        protein_node_type = "biolink:Protein"
        drug_protein_edge_label = "biolink:molecularly_interacts_with"
        drug_protein_edge_relation = "RO:0002436"  # molecularly interacts with
        self.edge_header = ['subject', 'edge_label', 'object', 'relation',
                            'provided_by', 'comment']

        with open(self.output_node_file, 'w') as node, \
                open(self.output_edge_file, 'w') as edge, \
                gzip.open(interactions_file, 'rt') as interactions:

            node.write("\t".join(self.node_header) + "\n")
            edge.write("\t".join(self.edge_header) + "\n")

            header_items = parse_header(interactions.readline())

            for line in interactions:
                items_dict = parse_drug_central_line(line, header_items)

                if 'ORGANISM' not in items_dict or items_dict['ORGANISM'] != species:
                    continue

                # get protein ID
                try:
                    protein_ids_string = get_item_by_priority(items_dict, ['ACCESSION'])
                    protein_ids = protein_ids_string.split('|')

                    if items_dict['DRUG_NAME'] == 'acetyldigitoxin':
                        pass
                except ItemInDictNotFound:
                    # lines with no ACCESSION entry only contain drug info, no target
                    # info - not ingesting these
                    continue

                # get drug ID
                drug_id = drug_curie_prefix + get_item_by_priority(items_dict,
                                                                   ['STRUCT_ID'])

                # WRITE NODES
                write_node_edge_item(fh=node,
                                     header=self.node_header,
                                     data=[drug_id,
                                           items_dict['DRUG_NAME'],
                                           drug_node_type,
                                           '',  # TDL (not applicable for drugs)
                                           self.source_name])

                for protein_id in protein_ids:
                    protein_id = uniprot_curie_prefix + protein_id

                    write_node_edge_item(fh=node,
                                         header=self.node_header,
                                         data=[protein_id,
                                               items_dict['GENE'],
                                               protein_node_type,
                                               items_dict['TDL'],
                                               self.source_name])

                    # WRITE EDGES
                    write_node_edge_item(fh=edge,
                                         header=self.edge_header,
                                         data=[drug_id,
                                               drug_protein_edge_label,
                                               protein_id,
                                               drug_protein_edge_relation,
                                               self.source_name,
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

    data = this_line.strip().split("\t")
    data = [i.replace('"', '') for i in data]
    item_dict = data_to_dict(header_items, data)

    return item_dict

