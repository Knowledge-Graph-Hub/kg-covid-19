#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import tempfile
import zipfile
from typing import List

import obonet  # type: ignore
from typing.io import TextIO  # type: ignore

from kg_covid_19.transform_utils.transform import Transform
from kg_covid_19.utils import write_node_edge_item
from kg_covid_19.utils.transform_utils import get_item_by_priority, data_to_dict, \
    ItemInDictNotFound, parse_header

"""Ingest PharmGKB drug -> drug target info

Dataset location: https://api.pharmgkb.org/v1/download/file/data/relationships.zip
GitHub Issue: https://github.com/Knowledge-Graph-Hub/kg-covid-19/issues/7

"""


class PharmGKBFileError(Exception):
    pass


class PharmGKB(Transform):

    def __init__(self, input_dir: str = None, output_dir: str = None):
        source_name = "pharmgkb"
        super().__init__(source_name, input_dir, output_dir)

    def run(self):
        zip_file_name = os.path.join(self.input_base_dir, "relationships.zip")
        relationship_file_name = "relationships.tsv"
        gene_node_type = "biolink:Protein"
        drug_node_type = "biolink:Drug"
        drug_gene_edge_label = "biolink:interacts_with"
        drug_gene_edge_relation = "RO:0002436"  # molecularly interacts with
        uniprot_curie_prefix = "UniProtKB:"

        tempdir = tempfile.mkdtemp()
        relationship_file_path = os.path.join(tempdir, relationship_file_name)
        self.unzip_to_tempdir(zip_file_name, tempdir)

        if not os.path.exists(relationship_file_path):
            raise PharmGKBFileError("Can't find relationship file needed for ingest")

        self.edge_header = ['subject', 'edge_label', 'object', 'relation']

        # transform relationship.tsv file
        with open(relationship_file_path) as relationships, \
                open(self.output_node_file, 'w') as node, \
                open(self.output_edge_file, 'w') as edge:
            # write headers (change default node/edge headers if necessary
            node.write("\t".join(self.node_header) + "\n")
            edge.write("\t".join(self.edge_header) + "\n")

            rel_header = parse_header(relationships.readline())
            for line in relationships:
                pass

    def unzip_to_tempdir(self, zip_file_name: str, tempdir: str):
        with zipfile.ZipFile(zip_file_name, 'r') as z:
            z.extractall(tempdir)

    def parse_pharmgkb_line(self, this_line: str) -> dict:
        pass

