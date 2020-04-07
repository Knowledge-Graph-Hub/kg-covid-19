#!/usr/bin/env python
# -*- coding: utf-8 -*-


import gzip
import logging
import os
import json

from typing import Dict, List

from kg_covid_19.transform_utils.transform import Transform
from kg_covid_19.utils.transform_utils import write_node_edge_item, \
    get_item_by_priority, ItemInDictNotFound, parse_header


DEFAULT_MAPPING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chembl_antiviral_drugs_mapping.json')

"""
Ingest antiviral data from ChEMBL

Essentially just ingests and transforms tab-delimited file derived from
the ChEMBL portal where you filter by ATC Class. Level 2 == 'ANTIVIRALS FOR SYSTEMIC USE'
"""

class ChEMBLAntiviralTransform(Transform):

    def __init__(self, **kwargs, input_dir: str = None, output_dir: str = None) -> None:
        source_name = "chembl_antiviral"
        super().__init__(source_name, input_dir, output_dir)  # set some variables

        self._mapping_lookup {}
        self._mapping_file = None
        self._target_node_to_header_lookup = {}
        self._target_node_to_etl_mapping_lookup = {}

        if 'mapping_file' in kwargs:
            #! TODO: Need to add support upstream client to allow for the mapping file to be passed into this constructor
            #? Is there no master configuration file to drive this software?
            
            self._mapping_file = kwargs['mapping_file']
        else:
            self._mapping_file = DEFAULT_MAPPING_FILE

    def _load_mapping_lookup(self) -> None:
        """Load the ETL mapping rules, defaults, etc. from the ETL mapping file
        :returns None:
        """
        mapping_file = self._mapping_file

        if not os.path.exists(mapping_file):
            logging.error("mapping file '{}' does not exist".format(mapping_file))
            sys.exit(1)
        
        self._mapping_lookup = json.loads(open(mapping_file.read())
        
        self._target_node_to_header_lookup = {}
        self._target_node_to_etl_mapping_lookup = {}

        for target_node in self._mapping_lookup:
            target_node_name = self._mapping_lookup['node name']
            if 'ordered column name list' not in self._mapping_lookup[target_node]:
                logging.error("'ordered column name list' does not exist in the target node with name '{}'".format(target_node_name))
                sys.exit(1)
            self._target_node_lookup[target_node_name] = self._mapping_lookup['ordered column name list']
            
            if 'ETL mapping' not in self._mapping_lookup[target_node]:
                logging.error("'ETL mapping' does not exist in the target node with name '{}'".format(target_node_name))
                sys.exit(1)
            self._target_node_to_etl_mapping_lookup[target_node_name] = self._mapping_lookup['ETL mapping']

        logging.info("Loaded the mapping lookup from mapping file '{}'".format(mapping_file))

    def run(self) -> None:
        """Method is called and performs needed transformations to 
        process the ChEMBL antiviral drug data, additional information
        on this data can be found in the comment at the top of this script
        """

        target_records_file = os.path.join(self.input_base_dir, "CHEMBL26-drug-antivirals.tsv.gz")
        os.makedirs(self.output_dir, exist_ok=True)

        self._load_mapping_lookup() 

        for target_node_name in self._target_node_to_etl_mapping_lookup.keys():

            logging.info("Processing data in '{}' to generate nodes of type '{}'".format(target_records_file, target_node_name))

            etl_mapping_lookup = self._target_node_to_etl_mapping_lookup[target_node_name]

            #! TODO: This can be better optimized to ensure the file is only read one time
            with open(self.output_node_file, 'w') as node, \
                    open(self.output_edge_file, 'w') as edge, \
                    gzip.open(target_records_file, 'rt') as target_records:


                self.node_header = self._target_node_to_header_lookup[target_node_name]

                node.write("\t".join(self.node_header) + "\n")

                header_items = parse_header(target_records.readline())
                
                for line in target_records:

                    items_dict = parse_drug_central_line(line, header_items)

                    #! TODO: Not the best choice of name 
                    node_data = [None] * len(self.node_header)

                    for i, node_field_name in enumerate(self.node_header):

                        if node_field_name not in etl_mapping_lookup:
                            logging.error("'{}' does not exist in the ETL mapping lookup for node type '{}'".format(node_field_name, target_node_name))
                            sys.exit(1)
                        
                        if 'source column' not in etl_mapping_lookup[node_field_name]:
                            logging.error("'source column' for target node field '{}' does not exist in the ETL mapping lookup for node type '{}'".format(node_field_name, target_node_name))
                            sys.exit(1)
                        
                        source_column_name = etl_mapping_lookup[node_field_name]['source column']
                        node_value = None

                        if source_column_name not in items_dict:
                            
                            if 'required' in etl_mapping_lookup[node_field_name] and etl_mapping_lookup[node_field_name]['required']:
                                logging.error("The required source column name '{}' does not exist in the items_dict for target node field name '{}' in target node type '{}'".format(source_column_name, node_field_name, target_node_name))
                                sys.exit(1)
                            else:
                                if 'default' not in etl_mapping_lookup[node_field_name]:
                                    logging.error("The 'default' does not exist in the ETL mapping for source column name '{}', target node field name '{}' in target node type '{}'".format(source_column_name, node_field_name, target_node_name))
                                    sys.exit(1)
                                else:
                                    node_value = etl_mapping_lookup[node_field_name]['default']
                        else:
                            if 'prefix' in etl_mapping_lookup[node_field_name]:
                                node_value = etl_mapping_lookup[node_field_name]['prefix'] + items_dict[etl_mapping_lookup[node_field_name]['source column']]
                            else:
                                node_value = items_dict[etl_mapping_lookup[node_field_name]['source column']]
                        
                        node_data[i] = node_value

                        write_node_edge_item(fh=node,
                                            header=self.node_header,
                                            node_data)

                        logging.info("Created '{}' target node for id '{}'".format(target_node_name, node_data[id]))

            return None



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

