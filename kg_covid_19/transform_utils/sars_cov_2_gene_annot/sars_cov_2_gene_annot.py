#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
from Bio.UniProt.GOA import gpa_iterator
from kg_covid_19.utils.transform_utils import get_item_by_priority
from typing.io import TextIO

from kg_covid_19.transform_utils.transform import Transform
from kg_covid_19.utils import write_node_edge_item

"""Parse the GPA and GPI files for SARS-CoV-2 gene annotations, including GO annotations
and more. Make a node for each gene using GPI lines, and make an edge for 
each gene -> annotation described in GPA 
"""


class SARSCoV2GeneAnnot(Transform):

    def __init__(self, input_dir: str = None, output_dir: str = None):
        source_name = "sars_cov_2_gene_annot"
        super().__init__(source_name, input_dir, output_dir)

        self.node_header = ['id', 'name', 'category', 'synonym', 'taxon']

        self.protein_node_type = "biolink:Protein"
        self.ncbi_taxon_prefix = "NCBITaxon:"

    def run(self):

        # file housekeeping
        os.makedirs(self.output_dir, exist_ok=True)

        gpi_file = os.path.join(self.input_base_dir, "uniprot_sars-cov-2.gpi")
        gpa_file = os.path.join(self.input_base_dir, "uniprot_sars-cov-2.gpa")

        with open(self.output_node_file, 'w') as node, \
                open(self.output_edge_file, 'w') as edge:


            # write headers
            node.write("\t".join(self.node_header) + "\n")
            edge.write("\t".join(self.edge_header) + "\n")

            with open(gpi_file, 'r') as gpi_fh:
                for rec in _gpi12iterator(gpi_fh):
                    self.gpi_to_gene_node(rec, node)

            with open(gpa_file, 'r') as gpa_fh:
                for rec in gpa_iterator(gpa_fh):
                    foo = 1

    def gpi_to_gene_node(self, rec: dict, node: TextIO) -> None:
        # ['id', 'name', 'category', 'synonym', 'taxon']
        data: list = []
        id = get_item_by_priority(rec, 'DB_Object_ID') + ":" + \
             get_item_by_priority(rec['DB_Object_Symbol'])
        try:
            name = get_item_by_priority(rec, 'DB_Object_Name')[0]
        except IndexError:
            name = ""
        category = self.protein_node_type
        synonym = get_item_by_priority(rec, 'DB_Object_Synonym')
        taxon = get_item_by_priority()
        write_node_edge_item(node, self.node_header, data)



def _gpi12iterator(handle: TextIO) -> dict:
    # cribbed from Biopython - no GPI 1.2 parser yet, so I made this
    """Read GPI 1.2 format files (PRIVATE).

    This iterator is used to read a gp_information.goa_uniprot
    file which is in the GPI 1.2 format.
    """
    # GPI version 1.2
    GPI11FIELDS = [
        "DB",
        "DB_Object_ID",
        "DB_Object_Symbol",
        "DB_Object_Name",
        "DB_Object_Synonym",
        "DB_Object_Type",
        "Taxon",
        "Parent_Object_ID",
        "DB_Xref",
        "Properties",
    ]
    for inline in handle:
        if inline[0] == "!":
            continue
        inrec = inline.rstrip("\n").split("\t")
        if len(inrec) == 1:
            continue
        inrec[2] = inrec[2].split("|")  # DB_Object_Name
        inrec[3] = inrec[3].split("|")  # DB_Object_Synonym(s)
        try:
            inrec[7] = inrec[7].split("|")  # DB_Xref(s)
        except IndexError:
            logging.debug("No index for DB_Xref for this record")
        try:
            inrec[8] = inrec[8].split("|")  # Properties
        except IndexError:
            logging.debug("No index for Properties for this record")

        yield dict(zip(GPI11FIELDS, inrec))
