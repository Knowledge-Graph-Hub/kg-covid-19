#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import re
import tempfile
from collections import defaultdict
from io import TextIOBase
from typing import Optional, TextIO

from kg_covid_19.transform_utils.transform import Transform
from kg_covid_19.utils.transform_utils import data_to_dict, parse_header, \
    unzip_to_tempdir, write_node_edge_item, get_item_by_priority, ItemInDictNotFound

"""Ingest PharmGKB drug -> drug target info

Dataset location: https://api.pharmgkb.org/v1/download/file/data/relationships.zip
GitHub Issue: https://github.com/Knowledge-Graph-Hub/kg-covid-19/issues/7

"""


class PharmGKB(Transform):

    def __init__(self, input_dir: str = None, output_dir: str = None):
        source_name = "pharmgkb"
        super().__init__(source_name, input_dir, output_dir)
        self.edge_header = ['subject', 'edge_label', 'object', 'relation',
                            'provided_by', 'type', 'evidence']
        self.node_header = ['id', 'name', 'category', 'provided_by']
        self.edge_of_interest = ['Gene',
                                 'Chemical']  # logic also matches 'Chemical'-'Gene'
        self.gene_node_type = "biolink:Gene"
        self.drug_node_type = "biolink:Drug"
        self.drug_gene_edge_label = "biolink:interacts_with"
        self.drug_gene_edge_relation = "RO:0002436"  # molecularly interacts with
        self.uniprot_curie_prefix = "UniProtKB:"

        self.uniprot_id_key = 'UniProtKB'  # id in genes.tsv where UniProt id is located
        self.key_parsed_ids = 'parsed_ids'  # key to put ids in after parsing

    def run(self, data_file: Optional[str] = None):
        rel_zip_file_name = os.path.join(self.input_base_dir, "relationships.zip")
        relationship_file_name = "relationships.tsv"
        gene_mapping_zip_file = os.path.join(self.input_base_dir, "pharmgkb_genes.zip")
        gene_mapping_file_name = "genes.tsv"
        drug_mapping_zip_file = os.path.join(self.input_base_dir, "pharmgkb_drugs.zip")
        drug_mapping_file_name = "drugs.tsv"

        #
        # file stuff
        #
        # get relationship file (what we are ingesting here)
        # TODO: unlink relationship_tempdir and gene_id_tempdir

        relationship_tempdir = tempfile.mkdtemp()
        relationship_file_path = os.path.join(relationship_tempdir,
                                              relationship_file_name)
        unzip_to_tempdir(rel_zip_file_name, relationship_tempdir)
        if not os.path.exists(relationship_file_path):
            raise PharmGKBFileError("Can't find relationship file needed for ingest")

        # get mapping file for gene ids
        gene_id_tempdir = tempfile.mkdtemp()
        gene_mapping_file_path = os.path.join(gene_id_tempdir,
                                              gene_mapping_file_name)
        unzip_to_tempdir(gene_mapping_zip_file, gene_id_tempdir)
        if not os.path.exists(gene_mapping_file_path):
            raise PharmGKBFileError("Can't find gene map file needed for ingest")
        self.gene_id_map = self.make_id_mapping_file(gene_mapping_file_path)

        # get mapping file for drug ids
        drug_id_tempdir = tempfile.mkdtemp()
        drug_mapping_file_path = os.path.join(drug_id_tempdir,
                                              drug_mapping_file_name)
        unzip_to_tempdir(drug_mapping_zip_file, drug_id_tempdir)

        if not os.path.exists(drug_mapping_file_path):
            raise PharmGKBFileError("Can't find drug map file needed for ingest")
        self.drug_id_map = self.make_id_mapping_file(drug_mapping_file_path)

        #
        # read in and transform relationship.tsv
        #
        with open(relationship_file_path) as relationships, \
                open(self.output_node_file, 'w') as node, \
                open(self.output_edge_file, 'w') as edge:
            # write headers (change default node/edge headers if necessary
            node.write("\t".join(self.node_header) + "\n")
            edge.write("\t".join(self.edge_header) + "\n")

            rel_header = parse_header(relationships.readline())
            for line in relationships:
                line_data = self.parse_pharmgkb_line(line, rel_header)

                if set(self.edge_of_interest) == \
                        set([line_data['Entity1_type'], line_data['Entity2_type']]):

                    #
                    # Make nodes for drug and chemical
                    #
                    for entity_id, entity_name, entity_type in [
                        [line_data['Entity1_id'], line_data['Entity1_name'],
                         line_data['Entity1_type']],
                        [line_data['Entity2_id'], line_data['Entity2_name'],
                         line_data['Entity2_type']]
                    ]:
                        if entity_type == 'Gene':
                            self.make_pharmgkb_gene_node(
                                                        fh=node,
                                                        this_id=entity_id,
                                                        name=entity_name,
                                                        biolink_type=self.gene_node_type)
                        elif entity_type == 'Chemical':
                            self.make_pharmgkb_chemical_node(
                                                        fh=node,
                                                        chem_id=entity_id,
                                                        name=entity_name,
                                                        biolink_type=self.drug_node_type)
                        else:
                            raise PharmKGBInvalidNodeType(
                                "Node type isn't gene or chemical!")

                    #
                    # Make edge
                    #
                    self.make_pharmgkb_edge(fh=edge,
                                            line_data=line_data)


    def make_preferred_drug_id(self, pharmgkb_id: str,
                               drug_id_map: dict,
                               preferred_ids: dict={'ChEBI:CHEBI': 'CHEBI',
                                                    'CHEMBL': 'CHEMBL',
                                                    'DrugBank': 'DRUGBANK',
                                                    'PubChem Compound:': 'PUBCHEM'},
                               pharmgkb_prefix: str='PHARMGKB') \
            -> str:
        """Given a drug id, convert it to a cross-referenced ID, in this order of
        preference:
         CHEBI > CHEMBL > DRUGBANK > PUBCHEM

        :param pharmgkb_id
        :param drug_id_map - map of pharmgkb ids to cross-referenced IDs
        :param preferred_ids - dict of preferred ids in desc order of preference
                'their string' -> 'canonical CURIE prefix'
                wow, they don't make this easy
        :param pharmgkb_prefix thing to prepend to pharmgkb id ('PHARMGKB')
        :return: preferred_id: preferred cross-referenced ID
        """
        preferred_id = pharmgkb_prefix + ":" + pharmgkb_id
        if pharmgkb_id in drug_id_map:
            if 'Cross-references' not in drug_id_map[pharmgkb_id]:
                logging.warning("Can't find 'Cross-references' item in drug_id_map! "
                                "Was it renamed?")
            elif not drug_id_map[pharmgkb_id]['Cross-references']:
                # 'Cross-references' is empty
                pass
            else:
                map_string = drug_id_map[pharmgkb_id]['Cross-references']

                # the following makes an atrocious string like
                # '"PREFIX1:1234', 'PREFIX2:3456'
                # into a dict I can pass to get_item_by_priority to look for preferred
                # ID
                these_cr_ids = map_string.split(",")
                these_cr_ids_dict: dict = defaultdict()
                for this_id in these_cr_ids:
                    this_id = re.sub(r'^"|"$', '', this_id)  # strip quotes
                    items = this_id.rpartition(':')
                    if len(items) >= 3:
                        these_cr_ids_dict[items[0]] = items[2]

                for pharmgkb_prefix, curie_prefix in preferred_ids.items():
                    try:
                        this_id = get_item_by_priority(these_cr_ids_dict, [pharmgkb_prefix])
                        preferred_id = curie_prefix + ":" + this_id
                        break
                    except ItemInDictNotFound:
                        pass

        return preferred_id


    def make_pharmgkb_edge(self,
                           fh: TextIO,
                           line_data: dict
                           ) -> None:

        if set(self.edge_of_interest) != \
                set([line_data['Entity1_type'], line_data['Entity2_type']]):
            raise PharmGKBInvalidEdge(
                "Trying to make edge that's not an edge of interest")

        if line_data['Entity1_type'] == 'Gene':
            gene_id = line_data['Entity1_id']
            drug_id = line_data['Entity2_id']
        else:
            gene_id = line_data['Entity2_id']
            drug_id = line_data['Entity1_id']

        gene_id = self.get_uniprot_id(this_id=gene_id)

        evidence = line_data['Evidence']

        preferred_drug_id = self.make_preferred_drug_id(drug_id, self.drug_id_map)

        data = [
            preferred_drug_id,
            self.drug_gene_edge_label,
            gene_id,
            self.drug_gene_edge_relation,
            self.source_name,
            'biolink:Association',
            evidence
        ]

        write_node_edge_item(fh=fh,
                             header=self.edge_header,
                             data=data)

    def make_pharmgkb_gene_node(self,
                                fh: TextIO,
                                this_id: str,
                                name: str,
                                biolink_type: str) -> None:
        """Write out node for gene
        :param fh: file handle to write out gene
        :param this_id: pharmgkb gene id
        :param name: gene name
        :param biolink_type: biolink type for Gene
        (from make_gene_id_mapping_file())
        :return: None
        """
        gene_id = self.get_uniprot_id(this_id=this_id)
        data = [gene_id, name, biolink_type, self.source_name]
        write_node_edge_item(fh=fh, header=self.node_header, data=data)

    def get_uniprot_id(self,
                       this_id: str,
                       pharmgkb_prefix: str='PHARMGKB'):
        try:
            gene_id = self.uniprot_curie_prefix + \
                      self.gene_id_map[this_id][self.key_parsed_ids][self.uniprot_id_key]
        except KeyError:
            gene_id = pharmgkb_prefix + ":" + this_id
        return gene_id

    def make_pharmgkb_chemical_node(self,
                                    fh: TextIO,
                                    chem_id: str,
                                    name: str,
                                    biolink_type: str
                                    ) -> None:
        """Write out node for gene
        :param fh: file handle to write out gene
        :param id: pharmgkb gene id
        :param name: gene name
        :param biolink_type: biolink type for Chemical
        :return: None
        """
        preferred_drug_id = self.make_preferred_drug_id(chem_id, self.drug_id_map)
        data = [preferred_drug_id, name, biolink_type, self.source_name]
        write_node_edge_item(fh=fh, header=self.node_header, data=data)

    def parse_pharmgkb_line(self, this_line: str, header_items) -> dict:
        """Parse a single line from relationships.tsv and return a dict with data

        :param this_line: line from relationship.tsv to parse
        :param header_items: header from relationships.tsv
        :return: dict with key value containing data
        """
        items = this_line.strip().split('\t')
        return data_to_dict(header_items, items)

    def make_id_mapping_file(self,
                             map_file: str,
                             sep: str = '\t',
                             pharmgkb_id_col: str = 'PharmGKB Accession Id',
                             id_key: str = 'Cross-references',
                             id_sep: str = ',',
                             id_key_val_sep: str = ':'
                             ) -> dict:
        """Fxn to parse gene ID mappings or drug ID mapping for PharmGKB ids
        This is to parse both genes.tsv and drugs.tsv files

        :param map_file: genes.tsv file, containing mappings
        :param pharmgkb_id_col: column containing pharmgkb, to be used as key for map
        :param sep: separator between columns [\t]
        :param id_key: column name that contains ids [Cross-references]
        :param id_sep: separator between each id key:val pair [,]
        :param id_key_val_sep: separator between key:val pair [:]
        :return:
        """
        map: dict = defaultdict()
        with open(map_file) as f:
            header_items = f.readline().split(sep)
            if pharmgkb_id_col not in header_items:
                raise CantFindPharmGKBKey("Can't find PharmGKB id in map file!")
            for line in f:
                items = line.strip().split(sep)
                dat = data_to_dict(header_items, items)
                if id_key in dat:
                    for item in dat[id_key].split(id_sep):
                        if not item:
                            continue  # not xrefs, skip
                        item = item.strip('\"')  # remove quotes around each item
                        key, value = item.split(id_key_val_sep, 1)  # split on first :
                        if self.key_parsed_ids not in dat:
                            dat[self.key_parsed_ids] = dict()
                        dat[self.key_parsed_ids][key] = value
                map[dat[pharmgkb_id_col]] = dat
        return map


class CantFindPharmGKBKey(Exception):
    pass


class PharmKGBInvalidNodeType(Exception):
    pass


class PharmGKBFileError(Exception):
    pass


class PharmGKBInvalidEdge(Exception):
    pass
