#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
from typing import Generator, TextIO, List, Optional

from kg_covid_19.utils.transform_utils import get_item_by_priority, ItemInDictNotFound, guess_bl_category

from kg_covid_19.transform_utils.transform import Transform
from kg_covid_19.utils import write_node_edge_item

"""Parse the GPA and GPI files for SARS-CoV-2 gene annotations, including GO annotations
and more. Make a node for each gene using GPI lines, and make an edge for 
each gene -> annotation described in GPA 
"""


class SARSCoV2GeneAnnot(Transform):

    def __init__(self, input_dir: Optional[str] = None, output_dir: str = None):
        source_name = "sars_cov_2_gene_annot"
        super().__init__(source_name, input_dir, output_dir)

        self.node_header = ['id', 'name', 'category', 'full_name', 'synonym',
                            'in_taxon', 'xrefs', 'provided_by']
        self.edge_header = ['subject', 'edge_label', 'object', 'relation',
                            'provided_by', 'type', 'DB_References', 'ECO_code', 'With',
                            'Interacting_taxon_ID',
                            'Date', 'Assigned_by', 'Annotation_Extension',
                            'Annotation_Properties']

        self.protein_node_type = "biolink:Protein"
        self.ncbi_taxon_prefix = "NCBITaxon"

        # translate edge labels to RO term, for the 'relation' column in edge
        self.edge_label_prefix = "biolink:"  # prepend to edge label
        self.edge_label_to_RO_term: dict = {
            'enables': 'RO:0002327',
            'involved_in': 'RO:0002331',
            'part_of': 'BFO:0000050'
        }

    def run(self, data_file: str = None):

        # file housekeeping
        os.makedirs(self.output_dir, exist_ok=True)

        gpi_file = os.path.join(self.input_base_dir, "uniprot_sars-cov-2.gpi")
        gpa_file = os.path.join(self.input_base_dir, "uniprot_sars-cov-2.gpa")

        with open(self.output_node_file, 'w') as node, \
                open(self.output_edge_file, 'w') as edge:

            # write headers
            node.write("\t".join(self.node_header) + "\n")
            edge.write("\t".join(self.edge_header) + "\n")
            seen = set()
            with open(gpi_file, 'r') as gpi_fh:
                for rec in _gpi12iterator(gpi_fh):
                    node_data = self.gpi_to_gene_node_data(rec)
                    seen.add(node_data[0])
                    write_node_edge_item(node, self.node_header, node_data)

            with open(gpa_file, 'r') as gpa_fh:
                for rec in _gpa11iterator(gpa_fh):
                    edge_data = self.gpa_to_edge_data(rec)
                    subject_node = edge_data[0]
                    if subject_node not in seen:
                        subject_node_data = [subject_node, guess_bl_category(subject_node)] + [""] * 5 + [self.source_name]
                        write_node_edge_item(node, self.node_header, subject_node_data)
                        seen.add(subject_node)
                    object_node = edge_data[2]
                    if object_node not in seen:
                        object_node_data = [object_node, guess_bl_category(object_node)] + [""] * 5 + [self.source_name]
                        write_node_edge_item(node, self.node_header, object_node_data)
                        seen.add(object_node)

                    write_node_edge_item(edge, self.edge_header, edge_data)

    def gpa_to_edge_data(self, rec: dict) -> list:
        """given a parsed gpa entry, return an edge with the annotations

        :param rec: record from gpa iterator
        :return:
        """
        subj: str = self._rec_to_id(rec)
        edge_label: str = get_item_by_priority(rec, ['Qualifier'])[0]
        obj: str = get_item_by_priority(rec, ['GO_ID'])
        try:
            relation: str = self.edge_label_to_RO_term[edge_label]
        except KeyError:
            relation = ''

        edge_data = [
            subj,
            self.edge_label_prefix + edge_label,
            obj,
            relation,
            self.source_name,
            'biolink:Association'
        ]

        # all the others
        for key in ['DB:Reference', 'ECO_Evidence_code', 'With', 'Interacting_taxon_ID',
                    'Date', 'Assigned_by', 'Annotation_Extension',
                    'Annotation_Properties']:
            try:
                item = get_item_by_priority(rec, [key])
                if type(item) is list:
                    item = item[0]
                if key == 'Interacting_taxon_ID':
                    item = ":".join([self.ncbi_taxon_prefix, item])
            except (ItemInDictNotFound, IndexError):
                item = ''
            edge_data.append(item)
        return edge_data

    def _rec_to_id(self, rec: dict) -> str:
        try:
            this_id: str = get_item_by_priority(rec, ['DB']) + ":" + \
                           get_item_by_priority(rec, ['DB_Object_ID'])
        except ItemInDictNotFound:
            logging.error("Can't make ID for record: %s", "\t".join(rec))
            this_id = ''
        return this_id

    def gpi_to_gene_node_data(self, rec: dict) -> list:
        """given a parsed gpi entry, return a node that can be passed to
        write_node_edge_item()

        :param rec: record from gpi iterator
        :return: list of node items, one for each thing in self.node_header
        """
        # ['id', 'name', 'category', 'full_name', 'synonym', 'in_taxon', 'xrefs', 'provided_by']
        id: str = self._rec_to_id(rec)

        try:
            name_list = get_item_by_priority(rec, ['DB_Object_Name'])
            if name_list is not None and len(name_list) > 0:
                full_name = name_list[0]
                if len(name_list) > 1:
                    logging.warning(
                        "Found >1 DB_Object_Name in rec, using the first one")
            else:
                full_name = ''
        except (IndexError, ItemInDictNotFound):
            full_name = ''

        try:
            symbol_list = get_item_by_priority(rec, ['DB_Object_Symbol'])
            if symbol_list is not None and len(symbol_list) > 0:
                name = symbol_list[0]
                if len(symbol_list) > 1:
                    logging.warning(
                        "Found >1 DB_Object_Symbol in rec, using the first one")
            else:
                name = ''
        except (IndexError, ItemInDictNotFound):
            full_name = ''

        category = self.protein_node_type
        try:
            synonym = get_item_by_priority(rec, ['DB_Object_Synonym'])
        except (IndexError, ItemInDictNotFound):
            synonym = ''
        taxon = get_item_by_priority(rec, ['Taxon'])
        taxon = ":".join([self.ncbi_taxon_prefix, taxon.split(":")[1]])

        xrefs = ''
        try:
            if rec['DB_Object_ID'] == 'UniProtKB:P0DTD1-PRO_0000449623':
                pass
            xrefs = get_item_by_priority(rec, ['DB_Xref'])
            if isinstance(xrefs, list):
                xrefs = "|".join(xrefs)
        except (ItemInDictNotFound):
            pass

        return [id, name, category, full_name, synonym, taxon, xrefs, self.source_name]


def _gpi12iterator(handle: TextIO) -> Generator:
    # Partly cribbed from Biopython GPI 1.1 parser
    # There is no GPI 1.2 parser yet, so I made this
    """Read GPI 1.2 format files (PRIVATE).

    This iterator is used to read a gp_information.goa_uniprot
    file which is in the GPI 1.2 format.
    """
    logging.getLogger().setLevel(logging.WARNING)
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
        inrec: List[str] = inline.rstrip("\n").split("\t")
        if len(inrec) == 1:
            continue
        # DB_Object_Name
        inrec[2] = inrec[2].split("|")  # type: ignore
        # DB_Object_Synonym(s)
        inrec[3] = inrec[3].split("|")  # type: ignore
        try:
            # DB_Xref(s)
            inrec[7] = inrec[7].split("|")  # type: ignore
        except IndexError:
            logging.debug("No index for DB_Xref for this record")
        try:
            # Properties
            inrec[8] = inrec[8].split("|")  # type: ignore
        except IndexError:
            logging.debug("No index for Properties for this record")

        yield dict(zip(GPI11FIELDS, inrec))


# from biopython, to avoid dependency
def _gpa11iterator(handle):
    """Read GPA 1.1 format files (PRIVATE).

    This iterator is used to read a gp_association.goa_uniprot
    file which is in the GPA 1.1 format. Do not call directly. Rather
    use the gpa_iterator function
    """
    # GPA version 1.1
    GPA11FIELDS = [
        "DB",
        "DB_Object_ID",
        "Qualifier",
        "GO_ID",
        "DB:Reference",
        "ECO_Evidence_code",
        "With",
        "Interacting_taxon_ID",
        "Date",
        "Assigned_by",
        "Annotation Extension",
        "Annotation_Properties",
    ]
    for inline in handle:
        if inline[0] == "!":
            continue
        inrec = inline.rstrip("\n").split("\t")
        if len(inrec) == 1:
            continue
        inrec[2] = inrec[2].split("|")  # Qualifier
        inrec[4] = inrec[4].split("|")  # DB:Reference(s)
        inrec[6] = inrec[6].split("|")  # With
        inrec[10] = inrec[10].split("|")  # Annotation extension
        yield dict(zip(GPA11FIELDS, inrec))
