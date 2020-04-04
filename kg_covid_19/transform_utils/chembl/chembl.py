#!/usr/bin/env python
# -*- coding: utf-8 -*-


import gzip
import logging
import os

from typing import Dict, List

from kg_covid_19.transform_utils.transform import Transform
from kg_covid_19.utils.transform_utils import write_node_edge_item, \
    get_item_by_priority, ItemInDictNotFound, parse_header

"""
Ingest target data from ChEMBL

Essentially just ingests and transforms tab-delimited file derived from
the ChEMBL portal where you filter by organism == 'Homo sapiens'
"""


DEFAULT_EXPECTED_FIELDS_LIST= ['ChEMBL ID', 'Name', 'UniProt Accessions', 'Type', 'Organism', 'Compounds', 'Activities', 'Tax ID', 'Species Group Flag']

DEFAULT_UNIPROT_ACCESSION_NAME = 'UNIPROT ACCESSION NAME TBD'
DEFAULT_UNIPROT_ACCESSION_CATEGORY = 'UNIPROT ACCESSION CATEGORY TBD'
        

DEFAULT_TARGET_TO_ACCESSION_EDGE_LABEL = 'TARGET TO UNIPROT ACCESSION EDGE LABEL TBD'
DEFAULT_TARGET_TO_ACCESSION_RELATION = 'TARGET TO UNIPROT ACCESSION RELATION TBD'
DEFAULT_TARGET_TO_ACTIVITY_EDGE_LABEL = 'TARGET TO ACTIVITY EDGE LABEL TBD'
DEFAULT_TARGET_TO_ACTIVITY_RELATION 'TARGET TO ACTIVITY RELATION TBD'


class ChEMBLTargetTransform(Transform):

    def __init__(self, input_dir: str = None, output_dir: str = None) -> None:
        source_name = "chembl_target"
        super().__init__(source_name, input_dir, output_dir)  # set some variables

        # Keep track of whether a node was created for a ChEMBL ID
        self._chembl_id_to_node_created_lookup = {}

        # Maintain a list of duplicate ChEMBL ID values
        self._duplicate_chembl_id_list = []

        # Tally number of duplicate ChEMBL ID values
        self._duplicate_chembl_id_ctr = 0

        # Ensure only one edge is created to link the ChEMBL ID to the UniProt Accession
        self._chembl_id_to_accession_lookup= {}

        # Ensure only one node is created for each unique UniProt Accession
        self._accession_to_node_created_lookup = {}

        # Ensure only one edge is created to link the ChEMBL ID to the Activity
        self._chembl_id_to_activity_lookup= {}

        # Ensure only one node is created for each unique activity
        self._activity_to_node_created_lookup = {}

    def run(self) -> None:
        """Method is called and performs needed transformations to process the ChEMBL target data, additional information
     on this data can be found in the comment at the top of this script"""

        target_records_file = os.path.join(self.input_base_dir, "chembl.target.tsv.gz")
        os.makedirs(self.output_dir, exist_ok=True)

        self._load_lookups()
        
        self.edge_header = ['subject', 'edge_label', 'object', 'relation']

        with open(self.output_node_file, 'w') as node, \
                open(self.output_edge_file, 'w') as edge, \
                gzip.open(target_records_file, 'rt') as target_records:

            node.write("\t".join(self.node_header) + "\n")
            edge.write("\t".join(self.edge_header) + "\n")

            header_items = parse_header(target_records.readline())

            for line in target_records:

                items_dict = parse_drug_central_line(line, header_items)

                # get gene ID
                try:
                    chembl_id = get_item_by_priority(items_dict, ['ChEMBL ID'])
                except ItemInDictNotFound:
                    # lines with no ACCESSION entry only contain drug info, no target
                    # info - not ingesting these
                    logging.info(
                        "No ChEMBL ID information for this line:\n{}\nskipping".format(line))
                    continue

                self._create_chembl_node(items_dict, line, line_ctr)
                self._create_organism_node_and_edge(chembl_id, items_dict)
                self._create_uniprot_accession_nodes_and_edges(chembl_id, items_dict)
                self._create_compound_nodes_and_edges(chembl_id, items_dict)
                self._create_activity_nodes_and_edges(chembl_id, items_dict)

        return None

    def _load_lookups(self) -> None:
        """Load all lookups
        :param None:
        :returns None:
        """
        self._load_expected_fields_lookup()
        self._load_field_to_biolink_mappings()

    def _load_field_to_biolink_mappings(self) -> None:
        """Load the field to biolink mapping lookup
        :param None:
        :returns None:
        """

        # drug_node_type = "biolink:Drug"
        # gene_node_type = "biolink:Gene"
        # drug_gene_edge_label = "biolink:interacts_with"
        # drug_gene_edge_relation = "RO:0002436"  # molecularly interacts with


        lookup = {'ChEMBL ID': '',
        'Name': '',
        'UniProt Accessions': '',
        'Type': '',
        'Organism': '',
        'Compounds': '',
        'Activities': '',
        'Tax ID': '',
        'Species Group Flag': ''}

        self._field_to_biolink_mapping_lookup = lookup
        logging.info("Loaded field to biolink mapping lookup")

    def _load_expected_fields_lookup(self) -> None:
        """Load the expected fields lookup
        :param None:
        :returns None:
        """
        self._expected_fields_lookup = {}
        for field in DEFAULT_EXPECTED_FIELDS_LIST:
            self._expected_fields_lookup[field] = True
        logging.info("Loaded fields lookup")

    def _create_chembl_node(self, items_dict: dict, line: str, line_ctr: int) -> None:
        """Create the node for the ChEMBL ID
        :param items_dict: {dict}
        :param line: {str}
        :param line_ctr: {int}
        :returns None:
        """

        if 'Name' in items_dict:
            if 'Type' in items_dict:
                if chembl_id not in self._chembl_id_to_node_created_lookup:
                    write_node_edge_item(fh=node,
                                        header=self.node_header,
                                        data=[chembl_id,
                                            items_dict['Name'],
                                            items_dict['Type']])
                    self._chembl_id_to_node_created_lookup[chembl_id] = True
                else:
                    logging.warning("Already created a node for ChEMBL ID '{}'".format(chembl_id))
                    self._duplicate_chembl_id_list.append(chembl_id)
                    self._duplicate_chembl_id_ctr += 1

            else:
                logging.warning("Unable to create node record for ChEMBL ID '{}' because 'Type' not found at line number '{}': {}".format(chembl_id, line_ctr, line))                        
        else:
            logging.warning("Unable to create node record for ChEMBL ID '{}' because 'Name' not found at line number '{}': {}".format(chembl_id, line_ctr, line))

    def _create_organism_node_and_edge(self, chembl_id: str, item_dict: dict) -> None:
        """Create the Organism node and the edge that will link it to the ChEMBL ID
        :param chembl_id: {str}
        :param item_dict: {dict}
        :returns None:
        """
        # Write the node for the Organism
        write_node_edge_item(fh=node,
                                header=self.node_header,
                                data=[gene_id,
                                    items_dict['GENE'],
                                    gene_node_type])

    def _create_uniprot_accession_nodes_and_edges(self, chembl_id : str, item_dict: dict) -> None:
        """Create the UniProt Accession nodes and the edges that will link it to the ChEMBL ID
        :param chembl_id: {str}
        :param item_dict: {dict}
        :returns None:
        """

        # Write the node for the UniProt Accessions
        uniprot_accession_list = self._get_uniprot_accession_list(items_dict['UniProt Accessions'])
        if len(uniprot_accession_list) > 0:
            for accession in uniprot_accession_list:
                if accession not in self._accession_to_node_created_lookup:
                    self._accession_to_node_created_lookup[accession] = True

                    (name, category) = self._get_uniprot_details_by_accession(accession)
                    write_node_edge_item(fh=node,
                                        header=self.node_header,
                                        data=[accession, name, category])
                else:
                    logging.info("Already created UniProt Accession node for accession '{}'".format(accession))

                # Create edge node to link the UniProt Accession to the Target
                # ['subject', 'edge_label', 'object', 'relation']
                if chembl_id not in self._chembl_id_to_accession_lookup:
                    self._chembl_id_to_accession_lookup[chembl_id] = {}

                if accession not in self._chembl_id_to_accession_lookup[chembl_id]:

                    edge_label = self._get_edge_label_for_target_to_accession()
                    relation = self._get_relation_for_target_to_accession()

                    write_node_edge_item(fh=edge,
                                        header=self.edge_header,
                                        data=[chembl_id,
                                            edge_label,
                                            accession,
                                            relation])

    def _get_uniprot_accession_list(self, accession: str) -> list:
        """Split the UniProt Accessions value and return a list
        :param accessions: {str}
        :returns accession_list: {list}
        """
        accession_list = None
        if accession.contain('|'):
            accession_list = accession.split('|')
        else:
            logging.info("Nothing to split in the accession value '{}'".format(accession))
            accession_list = accession
        return accession_list

    def _get_uniprot_details_by_accession(self, accession: str) -> tuple:
        """Derive the node name and node category for the UniProt Accession
        :param accession: {str}
        :returns name and category: {tuple}
        """
        name = DEFAULT_UNIPROT_ACCESSION_NAME
        category = DEFAULT_UNIPROT_ACCESSION_CATEGORY
        logging.warning("NOT YET IMPLEMENTED")
        return (name, category)

    def _create_compound_nodes_and_edges(self, chembl_id: str, items_dict: dict) -> None:
        """Create the UniProt Accession nodes and the edges that will link it to the ChEMBL ID
        :param chembl_id: {str}
        :param item_dict: {dict}
        :returns None:
        """

        # Write the node for the UniProt Accessions
        uniprot_accession_list = self._get_uniprot_accession_list(items_dict['UniProt Accessions'])
        if len(uniprot_accession_list) > 0:
            for accession in uniprot_accession_list:
                if accession not in self._accession_to_node_created_lookup:
                    (name, category) = self._get_uniprot_details_by_accession(accession)
                    write_node_edge_item(fh=node,
                                        header=self.node_header,
                                        data=[accession, name, category])
                else:
                    logging.info("Already created UniProt Accession node for accession '{}'".format(accession))

                # Create edge node to link the UniProt Accession to the Target
                # ['subject', 'edge_label', 'object', 'relation']
                if chembl_id not in self._chembl_id_to_accession_lookup:
                    self._chembl_id_to_accession_lookup[chembl_id] = {}

                if accession not in self._chembl_id_to_accession_lookup[chembl_id]:

                    edge_label = self._get_edge_label_for_target_to_accession()
                    relation = self._get_relation_for_target_to_accession()

                    write_node_edge_item(fh=edge,
                                        header=self.edge_header,
                                        data=[chembl_id,
                                            edge_label,
                                            accession,
                                            relation])
        
    def _create_activity_nodes_and_edges(self, chembl_id: str, items_dict: dict) -> None:
        """Create the Activity nodes and the edges that will link it to the ChEMBL ID
        :param chembl_id: {str}
        :param item_dict: {dict}
        :returns None:
        """
        if 'Activities' in items_dict:
            # Write the node for the Activity values
            activity_list = self._get_activity_list(items_dict['Activities'])
            if len(activity_list) > 0:
                for activity in activity_list:
                    if activity not in self._activity_to_node_created_lookup:
                        self._activity_to_node_created_lookup[activity] = True

                        (name, category) = self._get_activity_details_by_accession(activity_list)
                        write_node_edge_item(fh=node,
                                            header=self.node_header,
                                            data=[activity, name, category])
                    else:
                        logging.info("Already created Activity node for activity '{}'".format(activity))

                    # Create edge node to link the Activity to the Target
                    # ['subject', 'edge_label', 'object', 'relation']
                    if chembl_id not in self._chembl_id_to_activity_lookup:
                        self._chembl_id_to_activity_lookup[chembl_id] = {}

                    if activity not in self._chembl_id_to_activity_lookup[chembl_id]:

                        edge_label = self._get_edge_label_for_target_to_activity()
                        relation = self._get_relation_for_target_to_activity()

                        write_node_edge_item(fh=edge,
                                            header=self.edge_header,
                                            data=[chembl_id,
                                                edge_label,
                                                activity,
                                                relation])



    def _get_edge_label_for_target_to_accession(self, accession: str) -> str:
        """
        """
        edge_label = DEFAULT_TARGET_TO_ACCESSION_EDGE_LABEL
        logging.warning("NOT YET IMPLEMENTED")
        return edge_label

    def _get_relation_for_target_to_accession(self, accession: str) -> str:
        """
        """
        relation = DEFAULT_TARGET_TO_ACCESSION_RELATION
        logging.warning("NOT YET IMPLEMENTED")
        return relation

    def _get_edge_label_for_target_to_activity(self, activity: str) -> str:
        """
        """
        edge_label = DEFAULT_TARGET_TO_ACTIVITY_EDGE_LABEL
        logging.warning("NOT YET IMPLEMENTED")
        return edge_label

    def _get_relation_for_target_to_activity(self, activity: str) -> str:
        """
        """
        relation = DEFAULT_TARGET_TO_ACTIVITY_RELATION
        logging.warning("NOT YET IMPLEMENTED")
        return relation

def parse_drug_central_line(this_line: str, header_items: List) -> Dict:
    """Methods processes a line of text from Drug Central.

    Args:
        this_line: A string containing a line of text.
        header_items: A list of header items.

    Returns:
        item_dict: A dictionary of header items and a processed Drug Central string.
    """

    items = this_line.strip().split("\t")
    item_dict = dict(zip(header_items, items))

    return item_dict

