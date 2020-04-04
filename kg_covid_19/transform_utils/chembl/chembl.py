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

DEFAULT_QUALIFIED_ORGANISM_LIST = ['Homo Sapiens']

DEFAULT_TAXON_ID = 'N/A'

DEFAULT_ACCESSION_SEPARATOR = '|'
DEFAULT_COMPOUND_SEPARATOR = '|'
DEFAULT_ACTIVITY_SEPARATOR = '|'

class ChEMBLTargetTransform(Transform):

    def __init__(self, input_dir: str = None, output_dir: str = None) -> None:
        source_name = "chembl_target"
        super().__init__(source_name, input_dir, output_dir)  # set some variables

        self._accession_sep = DEFAULT_ACCESSION_SEPARATOR
        self._compound_sep = DEFAULT_COMPOUND_SEPARATOR
        self._activity_sep = DEFAULT_ACTIVITY_SEPARATOR
        
        self._qualified_organism_lookup = {}
        self._load_qualified_organism_lookup()

    def _load_qualified_organism_lookup(self) -> None:
        """Load the qualified organism lookup
        :returns None:
        """

        for organism in DEFAULT_QUALIFIED_ORGANISM_LIST:
            self._qualified_organism_lookup[organism] = True
        
        logging.info("Loaded the qualified organism lookup")

    def run(self) -> None:
        """Method is called and performs needed transformations to 
        process the ChEMBL target data, additional information
        on this data can be found in the comment at the top of this script
        """

        target_records_file = os.path.join(self.input_base_dir, "chembl.target.tsv.gz")
        os.makedirs(self.output_dir, exist_ok=True)

        self._load_lookups()
        
        self.edge_header = ['subject', 'edge_label', 'object', 'relation', 'activity']

        with open(self.output_node_file, 'w') as node, \
                open(self.output_edge_file, 'w') as edge, \
                gzip.open(target_records_file, 'rt') as target_records:

            node.write("\t".join(self.node_header) + "\n")
            edge.write("\t".join(self.edge_header) + "\n")

            header_items = parse_header(target_records.readline())

            for line in target_records:

                items_dict = parse_drug_central_line(line, header_items)

                if 'Organism' not in items_dict:
                    logging.info("The Organism does not exist so this record will be ignored")
                    continue

                if items_dict['Organism'] not in self._qualified_organism_lookup:
                    logging.info("The Organism '{}' does not exist in the qualified organism lookup so this record will be ignored".format(items_dict['Organism']))
                    continue

                # get gene ID
                try:
                    chembl_id = get_item_by_priority(items_dict, ['ChEMBL ID'])
                except ItemInDictNotFound:
                    # lines with no ACCESSION entry only contain drug info, no target
                    # info - not ingesting these
                    logging.info(
                        "No ChEMBL ID information for this line:\n{}\nskipping".format(line))
                    continue

                target_id_list = self._create_target_nodes(items_dict)

                compound_id_list = self._create_compound_nodes(items_dict)

                if 'Activities' in items_dict:
                    activity_list = self._get_activity_list(items_dict)
                else:
                    logging.info("No Activities for this record")
                    activity_list = ['N/A']

                for activity in activity_list:
                    for target_id in target_id_list:
                        for compound_id in compound_id_list:
                            self._create_target_compound_edge_node(target_id, compound_id, activity)

        return None

    def _get_activity_list(self, activities: str) -> list:
        """Derive the list of Activity values
        :param activities: {str}
        :returns activity_list: {list}
        """
        activity_list = []
        if self._activity_sep in activities:
            activity_list = activities.split(self._activity_sep)
        else:
            logging.error("Did not find '{}' separator in '{}'".format(self._activity_sep, activities))
            activity_list = [activities]
        return activity_list
    
    def _get_accession_list(self, accessions: str) -> list:
        """Derive the list of Accession values
        :param accessions: {str}
        :returns accession_list: {list}
        """
        accession_list = []
        if self._accession_sep in accessions:
            accession_list = accessions.split(self._accession_sep)
        else:
            logging.error("Did not find '{}' separator in '{}'".format(self._accession_sep, accessions))
            accession_list = [accessions]
        return accession_list

    def _get_compound_list(self, compounds: str) -> list:
        """Derive the list of Compound values
        :param compounds: {str}
        :returns compound_list: {list}
        """
        compound_list = []
        if self._compound_sep in compounds:
            compound_list = compounds.split(self._compound_sep)
        else:
            logging.error("Did not find '{}' separator in '{}'".format(self._compound_sep, compounds))
            compound_list = [compounds]
        return compound_list

    def _create_target_nodes(self, items_dict: dict) -> list:
        """Create the node for the target node
        :param items_dict: {dict}
        :returns target_id_list: {list}
        """

        # For target nodes:
        # id: a CURIE with Uniprot ID, e.g. UniProtKB:Q13547
        # name: whatever name chembl uses for the entry, or else just use the ID above
        # category: biolink:Protein
        # organism: NCBITaxon:XXXX (XXXX = 9606 if these are all human)

        target_id_list = []

        if 'UniProt Accessions' in items_dict:
        
            accession_list = self._get_accession_list(items_dict['UniProt Accessions'])
        
            if len(accession_list) > 0:
                for accession in accession_list:
                    id = 'UniProtKB:' + accession
                    name = items_dict['Name']
                    category = 'biolink:Protein'
                    organism = self._get_organism_taxon(items_dict['Organism'])

                    write_node_edge_item(fh=node,
                                        header=self.node_header,
                                        data=[id, name, category, organism])
                    logging.info("Created target node for id '{}' name '{}' category '{}' organism '{}'".format(id, name, category, organism))
                    target_id_list.append(id)
            else:
                logging.info("Not accessions to process for this record")
        else:
            logging.info("UniProt Accessions does not exist in the items_dict")

        return target_id_list

    def _get_organism_taxon(self, organism: str) -> str:
        """Retrieve the taxon for the organism.
        Currently, only supporting organism == 'Homo sapiens'.
        :param organism: {str}
        :returns taxon_id: {str}
        """
        taxon = DEFAULT_TAXON_ID
        if organism == 'Homo sapiens':
            taxon_id = 'NCBITaxon:9606'
        else:
            logging.error("organism '{}' is not currently supported".format(organism))
        return taxon_id

    def _create_compound_nodes(self, item_dict: dict) -> list:
        """Create nodes for the compound
        :param item_dict: {dict}
        :returns compound_id_list: {list}
        """
        # For compound (drug) nodes:
        # id: a CURIE for the drug using CHEMBL ID, e.g. CHEMBL:12345
        # name: whatever name chembl uses for the entry, or else just use the ID above
        # category: biolink:Drug
        # organism: NCBITaxon:XXXX (XXXX = 9606 if these are all human)
        
        compound_id_list = []

        if 'Compounds' in item_dict:
            compound_list = self._get_component_list(items_dict['Compounds'])
            if len(compound_list) > 0:
                for compound in compound_list:

                    id = 'CHEMBL:' + item_dict['ChEMBL ID']
                    name = items_dict['Name']
                    category = 'biolink:Drug'
                    organism = self._get_organism_taxon(items_dict['Organism'])

                    write_node_edge_item(fh=node,
                                        header=self.node_header,
                                        data=[id, name, category, organism])

                    compound_id_list.append(id)
                    logging.info("Created compound node for id '{}' name '{}' category '{}' organism '{}'".format(id, name, category, organism))
            else:
                logging.info("Not compounds to process for this record")
        else:
            logging.info("Compounds does not exist in the items_dict")
        
        return compound_id_list

    def _create_target_compound_edge_node(self, target_id: str, compound_id: str, activity: str) -> None:
        """
        """
        edge_label = 'biolink:interacts_with'
        relation = 'RO:0002436'
        
        write_node_edge_item(fh=edge,
                            header=self.edge_header,
                            data=[target_id, edge_label, compound_id, relation, activity])


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

