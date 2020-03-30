#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
from collections import defaultdict

from kg_covid_19.transform_utils.transform import Transform

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

        ttd_file_name = os.path.join(self.input_base_dir,
                                     "P1-01-TTD_target_download.txt")
        ttd_data = self.parse_ttd_file(ttd_file_name)

        # transform data, something like:
        with open(self.output_node_file, 'w') as node,\
                open(self.output_edge_file, 'w') as edge:

            # write headers (change default node/edge headers if necessary
            node.write("\t".join(self.node_header) + "\n")
            edge.write("\t".join(self.edge_header) + "\n")

            foo = 1

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
        parsed_data = dict()

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

                (field1, field2, field3) = self.parse_line(line)

                if field1 not in parsed_data:
                    parsed_data[field1] = dict()

                if field2 not in parsed_data[field1]:
                    parsed_data[field1][field2] = []

                parsed_data[field1][field2].append(field3)

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
        data_list = fields[2:]

        return [target_id, abbrev, data_list]
