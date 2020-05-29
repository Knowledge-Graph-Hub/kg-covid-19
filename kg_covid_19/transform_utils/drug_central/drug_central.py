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

And extracts Drug -> Gene interactions
"""


class DrugCentralTransform(Transform):

    def __init__(self, input_dir: str = None, output_dir: str = None) -> None:
        source_name = "drug_central"
        super().__init__(source_name, input_dir, output_dir)  # set some variables
        self.node_header = ['id', 'name', 'category', 'tclin', 'tchem']

    def run(self, data_file: Optional[str] = None, species: str = "Homo sapiens") -> None:
        """Method is called and performs needed transformations to process the Drug
        Central data, additional information
        on this data can be found in the comment at the top of this script"""

        interactions_file = os.path.join(self.input_base_dir,
                                         "drug.target.interaction.tsv.gz")
        tclin_chem_zip_file = os.path.join(self.input_base_dir, "tcrd.zip")
        os.makedirs(self.output_dir, exist_ok=True)
        drug_node_type = "biolink:Drug"
        gene_curie_prefix = "UniProtKB:"
        drug_curie_prefix = "DrugCentral:"
        gene_node_type = "biolink:Gene"
        drug_gene_edge_label = "biolink:interacts_with"
        drug_gene_edge_relation = "RO:0002436"  # molecularly interacts with
        self.edge_header = ['subject', 'edge_label', 'object', 'relation',
                            'provided_by', 'comment']

        # unzip tcrd.zip and get tchem and tclin filenames
        tempdir = tempfile.mkdtemp()
        (tclin_file, tchem_file) = unzip_and_get_tclin_tchem(tclin_chem_zip_file, tempdir)

        tclin_dict: dict = tsv_to_dict(tclin_file, 'uniprot')
        tchem_dict: dict = tsv_to_dict(tchem_file, 'uniprot')

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

                # get gene ID
                try:
                    gene_id_string = get_item_by_priority(items_dict, ['ACCESSION'])
                    gene_ids = gene_id_string.split('|')
                except ItemInDictNotFound:
                    # lines with no ACCESSION entry only contain drug info, no target
                    # info - not ingesting these
                    continue

                # get drug ID
                drug_id = drug_curie_prefix + get_item_by_priority(items_dict,
                                                                   ['STRUCT_ID'])

                # WRITE NODES
                # drug - ['id', 'name', 'category']
                write_node_edge_item(fh=node,
                                     header=self.node_header,
                                     data=[drug_id,
                                           items_dict['DRUG_NAME'],
                                           drug_node_type,
                                           str(False),
                                           str(False)])

                for gene_id in gene_ids:
                    gene_id = gene_curie_prefix + gene_id
                    is_tclin = True if gene_ids[0] in tclin_dict else False
                    is_tchem = True if gene_ids[0] in tchem_dict else False

                    write_node_edge_item(fh=node,
                                         header=self.node_header,
                                         data=[gene_id,
                                               items_dict['GENE'],
                                               gene_node_type,
                                               str(is_tclin),
                                               str(is_tchem)])

                    # WRITE EDGES
                    # ['subject', 'edge_label', 'object', 'relation', 'provided_by',
                    # 'comment']
                    write_node_edge_item(fh=edge,
                                         header=self.edge_header,
                                         data=[drug_id,
                                               drug_gene_edge_label,
                                               gene_id,
                                               drug_gene_edge_relation,
                                               self.source_name,
                                               items_dict['ACT_COMMENT']])

        return None


def tsv_to_dict(input_file: str, col_for_key: str) -> dict:
    this_dict: dict = defaultdict(list)
    with open(input_file) as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            this_dict[row[col_for_key]] = row
    return this_dict


def unzip_and_get_tclin_tchem(zip_file: str, output_dir: str) -> List[str]:
    unzip_to_tempdir(zip_file, output_dir)
    # get tclin filename
    tclin_files = \
        [f for f in os.listdir(output_dir) if re.match(r'tclin_.*\.tsv', f)]
    if len(tclin_files) > 1:
        raise RuntimeError("Found more than one tclin file:\n%s" %
                           "\n".join(tclin_files))
    elif len(tclin_files) < 1:
        raise RuntimeError("Couldn't find tclin file in zipfile %s" % zip_file)
    else:
        tclin_file: str = os.path.join(output_dir, tclin_files[0])

    # get tchem filename
    tchem_files = \
        [f for f in os.listdir(output_dir) if re.match(r'tchem_.*\.tsv', f)]
    if len(tchem_files) > 1:
        raise RuntimeError("Found more than one tchem file:\n%s" %
                           "\n".join(tchem_files))
    elif len(tchem_files) < 1:
        raise RuntimeError("Couldn't find tchem file in zipfile %s" % zip_file)
    else:
        tchem_file: str = os.path.join(output_dir, tchem_files[0])

    return [tclin_file, tchem_file]


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

