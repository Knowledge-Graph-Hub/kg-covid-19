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

    def run(self, data_file: Optional[str] = None,
            species: str = "Homo sapiens") -> None:
        """Method is called and performs needed transformations to process the Drug
        Central data, additional information
        on this data can be found in the comment at the top of this script"""

        if data_file is None:
            data_file = "drug.target.interaction.tsv.gz"
        interactions_file = os.path.join(self.input_base_dir,
                                         data_file)
        os.makedirs(self.output_dir, exist_ok=True)
        drug_node_type = "biolink:Drug"
        uniprot_curie_prefix = "UniProtKB:"
        drug_curie_prefix = "DrugCentral:"
        protein_node_type = "biolink:Protein"
        drug_protein_edge_label = "biolink:molecularly_interacts_with"
        drug_protein_edge_relation = "RO:0002436"  # molecularly interacts with
        self.edge_header = ['subject', 'edge_label', 'object', 'relation',
                            'provided_by', 'comment', 'type']

        with open(self.output_node_file, 'w') as node, \
                open(self.output_edge_file, 'w') as edge, \
                gzip.open(interactions_file, 'rt') as interactions:

            node.write("\t".join(self.node_header) + "\n")
            edge.write("\t".join(self.edge_header) + "\n")

            header_items = parse_header(interactions.readline())

            seen_proteins: dict = defaultdict(int)
            seen_drugs: dict = defaultdict(int)

            for line in interactions:
                items_dict = parse_drug_central_line(line, header_items)

                if 'ORGANISM' not in items_dict or items_dict['ORGANISM'] != species:
                    continue

                # get protein ID
                try:
                    protein_dict = items_dict_to_protein_data_dict(items_dict)

                except ItemInDictNotFound:
                    # lines with no ACCESSION entry only contain drug info, no target
                    # info - not ingesting these
                    continue
                except ValueError:
                    logging.error("Value error while parsing line")
                    continue

                # get drug ID
                drug_id = drug_curie_prefix + get_item_by_priority(items_dict,
                                                                   ['STRUCT_ID'])

                # Write drug node
                if drug_id not in seen_drugs:
                    write_node_edge_item(fh=node,
                                         header=self.node_header,
                                         data=[drug_id,
                                               items_dict['DRUG_NAME'],
                                               drug_node_type,
                                               '',  # TDL (not applicable for drugs)
                                               self.source_name])
                    seen_drugs[drug_id] += 1

                for key, (uniprot_id, name, tdl) in protein_dict.items():
                    protein_id = uniprot_curie_prefix + uniprot_id

                    if protein_id not in seen_proteins:
                        write_node_edge_item(fh=node,
                                             header=self.node_header,
                                             data=[protein_id,
                                                   name,
                                                   protein_node_type,
                                                   tdl,
                                                   self.source_name])
                        seen_proteins[protein_id] += 1

                    # WRITE EDGES
                    write_node_edge_item(fh=edge,
                                         header=self.edge_header,
                                         data=[drug_id,
                                               drug_protein_edge_label,
                                               protein_id,
                                               drug_protein_edge_relation,
                                               self.source_name,
                                               items_dict['ACT_COMMENT'],
                                               'biolink:Association'])

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


def items_dict_to_protein_data_dict(items_dict: dict) -> dict:
    """Given a parsed line from parse_drug_central_line, split up pipe-separated entries
    for several related proteins and their names and TDL info into separate protein
    entries

    :param items_dict: dictionary of data from a line, output by parse_drug_central_line
    :return: a dict with information about each protein
    """
    protein_ids_string = get_item_by_priority(items_dict, ['ACCESSION'])
    protein_ids = protein_ids_string.split('|')
    gene_name = get_item_by_priority(items_dict, ['GENE']).split('|')
    TDL_values = get_item_by_priority(items_dict, ['TDL']).split('|')

    if len(protein_ids) != len(gene_name):
        logging.warning("Didn't get the same number of entries for protein_ids and gene_ids")
        gene_name = [''] * len(protein_ids)

    if len(protein_ids) != len(TDL_values):
        # this happens - repeat TDL designation for all protein IDs
        TDL_values = TDL_values * len(protein_ids)

    protein_dict = defaultdict(list)
    for i in range(len(protein_ids)):
        protein_dict[protein_ids[i]] = [protein_ids[i], gene_name[i], TDL_values[i]]
    return protein_dict
