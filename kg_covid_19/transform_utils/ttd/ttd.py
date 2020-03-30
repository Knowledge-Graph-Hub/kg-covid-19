#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from kg_covid_19.transform_utils.transform import Transform

"""Ingest TTD - Therapeutic Targets Database
# drug targets, and associated data for each (drugs, ids, etc)
#
Dataset location: http://db.idrblab.net/ttd/sites/default/files/ttd_database/P1-01-TTD_target_download.txt
GitHub Issue: https://github.com/Knowledge-Graph-Hub/kg-covid-19/issues/6
"""


class TTDTransform(Transform):

    def __init__(self):
        super().__init__(source_name="ttd")

    def run(self) -> None:
        # make directory in data/transformed
        os.makedirs(self.output_dir, exist_ok=True)

        ttd_file_name = os.path.join(self.input_base_dir, "P1-01-TTD_target_download.txt")

        # transform data, something like:
        with open(ttd_file_name, 'r') as ttd_file, \
                open(self.output_node_file, 'w') as node, \
                open(self.output_edge_file, 'w') as edge:

            # write headers (change default node/edge headers if necessary
            node.write("\t".join(self.node_header) + "\n")
            edge.write("\t".join(self.edge_header) + "\n")

    def parse_ttd_file(self, file: str) -> object:
        """Parse entire TTD download file (a few megs, not very mem efficient, but
        should be okay), and return a dict of dicts

        [target_id] -> [abbreviation] -> [list with data]

        where 'abbreviation' is one of:

        TARGETID	TTD Target ID
        FORMERID	TTD Former Target ID
        UNIPROID	Uniprot ID
        TARGNAME	Target Name
        GENENAME	Target Gene Name
        TARGTYPE	Target Type
        SYNONYMS	Synonyms
        FUNCTION	Function
        PDBSTRUC	PDB Structure
        BIOCLASS	BioChemical Class
        ECNUMBER	EC Number
        SEQUENCE	Sequence
        DRUGINFO	TTD Drug ID	Drug Name	Highest Clinical Status
        KEGGPATH	KEGG Pathway
        WIKIPATH	WiKipathway
        WHIZPATH	PathWhiz Pathway
        REACPATH	Reactome Pathway
        NET_PATH	NetPathway
        INTEPATH	Pathway Interact
        PANTPATH	PANTHER Pathway
        BIOCPATH	BioCyc

        :param file
        :return: dict of dicts of lists
        """
        return dict()

