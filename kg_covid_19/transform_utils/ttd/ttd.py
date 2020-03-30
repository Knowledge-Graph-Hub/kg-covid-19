#!/usr/bin/env python
# -*- coding: utf-8 -*-
import collections
import logging
import os
import re
from typing import Union, List, Dict, Any

from kg_covid_19.transform_utils.transform import Transform
from kg_covid_19.utils import write_node_edge_item
from kg_covid_19.utils.transform_utils import get_item_by_priority, ItemInDictNotFound

"""Ingest TTD - Therapeutic Targets Database
# drug targets, and associated data for each (drugs, ids, etc)
#
Dataset location: http://db.idrblab.net/ttd/sites/default/files/ttd_database/P1-01-TTD_target_download.txt
GitHub Issue: https://github.com/Knowledge-Graph-Hub/kg-covid-19/issues/6
"""


class TTDNotEnoughFields(Exception):
    pass


class TTDTransform(Transform):

    def __init__(self):
        super().__init__(source_name="ttd")

    def run(self) -> None:
        # make directory in data/transformed
        os.makedirs(self.output_dir, exist_ok=True)

        self.node_header.append("TTD_ID") # append ttd id for drug targets and drugs
        ttd_file_name = os.path.join(self.input_base_dir,
                                     "P1-01-TTD_target_download.txt")
        ttd_data = self.parse_ttd_file(ttd_file_name)
        gene_node_type = "biolink:Gene"
        drug_node_type = "biolink:Drug"
        drug_gene_edge_label = "biolink:interacts_with"
        drug_gene_edge_relation = "RO:0002436"  # molecularly interacts with

        self.edge_header = ['subject', 'edge_label', 'object', 'relation', 'target_type']

        # transform data, something like:
        with open(self.output_node_file, 'w') as node,\
                open(self.output_edge_file, 'w') as edge:

            # write headers (change default node/edge headers if necessary
            node.write("\t".join(self.node_header) + "\n")
            edge.write("\t".join(self.edge_header) + "\n")

            for target_id, data in ttd_data.items():
                # WRITE NODES

                # skip items that don't refer to UNIPRO gene targets or don't have
                # drug info
                if 'UNIPROID' not in data:
                    logging.info("Skipping item that doesn't refer to UNIPROT gene")
                    continue
                if 'DRUGINFO' not in data:
                    logging.info("Skipping item that doesn't have any drug info")
                    continue

                #
                # make node for gene
                #
                try:
                    uniproids = get_item_by_priority(data, ['UNIPROID'])
                    uniproid = uniproids[0]
                except ItemInDictNotFound:
                    logging.warning("Problem with UNIPROID for this target id {}".format(data))

                try:
                    gene_names = get_item_by_priority(data, ['GENENAME'])
                    gene_name = gene_names[0]
                except ItemInDictNotFound:
                    logging.warning("Problem with UNIPROID for this target id  {}".format(data))

                # gene - ['id', 'name', 'category', 'ttd id for this target']
                write_node_edge_item(fh=node,
                                     header=self.node_header,
                                     data=[uniproid,
                                           gene_name,
                                           gene_node_type,
                                           target_id
                                           ])

                # for each drug in DRUGINFO:
                for this_drug in data['DRUGINFO']:
                    #
                    # make node for drug
                    #
                    write_node_edge_item(fh=node,
                                         header=self.node_header,
                                         data=[this_drug[0],
                                               this_drug[1],
                                               drug_node_type,
                                               this_drug[0]
                                               ])

                    #
                    # make edge for target <-> drug
                    #

                    targ_type = ""
                    try:
                        targ_types = get_item_by_priority(data, ['TARGTYPE'])
                        targ_type = targ_types[0]
                    except ItemInDictNotFound:
                        pass

                    # ['subject', 'edge_label', 'object', 'relation', 'comment']
                    write_node_edge_item(fh=edge,
                                         header=self.edge_header,
                                         data=[target_id,
                                               drug_gene_edge_label,
                                               uniproid,
                                               drug_gene_edge_relation,
                                               targ_type])

    def parse_ttd_file(self, file: str) -> dict:
        """Parse entire TTD download file (a few megs, not very mem efficient, but
        should be okay), and return a dict of dicts of lists

        [target_id] -> [abbreviation] -> [list with data]

        where 'abbreviation' is one of:
        ['TARGETID', 'FORMERID', 'UNIPROID', 'TARGNAME', 'GENENAME', 'TARGTYPE',
         'SYNONYMS', 'FUNCTION', 'PDBSTRUC', 'BIOCLASS', 'ECNUMBER', 'SEQUENCE',
         'DRUGINFO', 'KEGGPATH', 'WIKIPATH', 'WHIZPATH', 'REACPATH', 'NET_PATH',
         'INTEPATH', 'PANTPATH', 'BIOCPATH']

        :param file
        :return: dict of dicts of lists
        """
        parsed_data = collections.defaultdict(dict) # type: ignore

        # wish they'd make this file easier to parse
        seen_dashed_lines = 0
        dashed_line_re = re.compile(r'^-+\n')
        blank_line_re = re.compile(r'^\s*$')

        with open(file, 'r') as fh:
            for line in fh:
                if dashed_line_re.match(line):
                    seen_dashed_lines = seen_dashed_lines + 1
                    continue

                if seen_dashed_lines < 2 or blank_line_re.match(line):
                    continue

                (target_id, abbrev, data_list) = self.parse_line(line)

                if target_id not in parsed_data:
                    parsed_data[target_id] = dict()

                if abbrev not in parsed_data[target_id]:
                    parsed_data[target_id][abbrev] = []

                parsed_data[target_id][abbrev].append(data_list)

        return parsed_data

    def parse_line(self, line: str) -> list:
        """Parse one line of data from  P1-01-TTD_target_download, and return
        list comprised of:

        [target_id, abbrev, data_list]

        where:
        target_id is the target_id
        abbrev is a member of 'TARGETID', 'FORMERID', etc] (see above)
        data_list is a list of all items in field3 ... last field, split on '\t'

        :param line: line from P1-01-TTD_target_download
        :return: [target_id, abbrev, data_list]
        """
        fields = line.rstrip().split('\t')
        if len(fields) < 3:
            raise TTDNotEnoughFields("Not enough fields in line {}".format(line))
        target_id = fields[0]
        abbrev = fields[1]

        data: Union[List, str]
        if len(fields[2:]) == 1:
            data = fields[2]
        else:
            data = fields[2:]

        return [target_id, abbrev, data]
