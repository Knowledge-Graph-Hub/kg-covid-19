#!/usr/bin/env python
# -*- coding: utf-8 -*-
import fnmatch
import logging
import os
import re
import tempfile
from collections import defaultdict
from typing import Union, Dict, List

from kg_covid_19.transform_utils.transform import Transform
from kg_covid_19.utils.transform_utils import write_node_edge_item, unzip_to_tempdir
from xml.dom import minidom  # type: ignore

"""
Ingest IntAct protein/protein interaction data 
https://www.ebi.ac.uk/intact/
specifically about coronavirus viral protein/host protein interactions. 

The file at this URL:
https://t.co/OUGKWbpQHG?amp=1
is zip file containing XML files that describe coronavirus interactions shown in a
publication. 

Each XML file is a miXML following this spec: 
https://github.com/HUPO-PSI/miXML
"""


class IntAct(Transform):

    def __init__(self, input_dir: str = None, output_dir: str = None) -> None:
        source_name = "intact"
        super().__init__(source_name, input_dir, output_dir)
        # interactor type to biolink category
        bl_rna_cat = 'biolink:RNA'
        self.type_to_biolink_category = {
            'protein': 'biolink:Protein',
            'rna': bl_rna_cat,
            'mrna': bl_rna_cat,
            'snrna': bl_rna_cat
        }
        self.db_to_prefix = {
            'uniprot': 'UniProtKB',
            'uniprotkb': 'UniProtKB',
            'chebi': 'CHEBI',
            'ensembl': 'ENSEMBL',
            'ddbj/embl/genbank': 'NCBIProtein',
            'pubmed': 'PMID'
        }
        self.pubmed_curie_prefix = 'PMID:'
        self.ppi_edge_label = 'biolink:interacts_with'
        self.ppi_ro_relation = 'RO:0002437'
        self.edge_header = ['subject', 'edge_label', 'object', 'relation',
                            'num_participants', 'association_type', 'detection_method',
                            'publication']

    def run(self) -> None:
        """Method to run transform to ingest data from IntAct for viral/human PPIs"""

        zip_file = os.path.join(self.input_base_dir, 'intact_coronavirus.zip')

        # for tsv output:
        output_node_file = os.path.join(self.output_dir, 'nodes.tsv')
        output_edge_file = os.path.join(self.output_dir, 'edges.tsv')

        # make directory in data/transformed
        os.makedirs(self.output_dir, exist_ok=True)

        with open(output_node_file, 'w') as node, \
                open(output_edge_file, 'w') as edge:

            # write node.tsv header
            node.write('\t'.join(self.node_header) + '\n')
            edge.write('\t'.join(self.edge_header) + '\n')

            xml_tempdir = tempfile.mkdtemp()
            unzip_to_tempdir(zip_file, xml_tempdir)

            extracted_base_dir_list = os.listdir(xml_tempdir)
            file_path = os.path.join(xml_tempdir, extracted_base_dir_list[0])
            for file in os.listdir(file_path):
                if not fnmatch.fnmatch(file, '*.xml'):
                    logging.warning("Skipping non-xml file %s" % file)

                nodes_edges = self.parse_xml_to_nodes_edges(
                    os.path.join(file_path, file))

                # write out nodes
                for this_node in nodes_edges['nodes']:
                    write_node_edge_item(fh=node,
                                         header=self.node_header,
                                         data=this_node)
                # write out edges
                for this_edge in nodes_edges['edges']:
                    write_node_edge_item(fh=edge,
                                         header=self.edge_header,
                                         data=this_edge)

    def parse_xml_to_nodes_edges(self, xml_file: str) -> dict:
        parsed: Dict[str, list] = dict()
        parsed['nodes'] = []
        parsed['edges'] = []

        xmldoc = minidom.parse(xml_file)

        #
        # nodes
        #

        # store by interactor id, since this is what is referenced in edges
        nodes_dict = dict()
        for interactor in xmldoc.getElementsByTagName('interactor'):
            (int_id, node_data) = self.interactor_to_node(interactor)
            nodes_dict[int_id] = node_data

        experiment_dict = self.parse_experiment_info(xmldoc)

        # write nodes
        for key, value in nodes_dict.items():
            parsed['nodes'].append(value)

        #
        # edges
        #
        for interaction in xmldoc.getElementsByTagName('interaction'):
            edge_data = self.interaction_to_edge(interaction, nodes_dict,
                                                 experiment_dict)
            if edge_data is not None:
                parsed['edges'].append(edge_data)

        return parsed

    def interaction_to_edge(self, interaction: object, nodes_dict: dict,
                            exp_dict: dict) -> Union[list, None]:
        interactor1 = ""
        interactor2 = ""
        try:
            # TODO: deal with cases where interactors != 2
            interaction_type = interaction.getElementsByTagName('interactionType')  # type: ignore
            interaction_type_str = interaction_type[0].getElementsByTagName(
            "shortLabel")[0].firstChild._data

            interactors = interaction.getElementsByTagName("interactorRef")  # type: ignore
            if len(interactors) < 2:  # this isn't interaction data
                return None
            if len(interactors) > 2:  # hmm
                logging.warning("More than 2 interactors in interactions")
                return None

            interactor1 = nodes_dict[interactors[0].firstChild.data][0]
            interactor2 = nodes_dict[interactors[1].firstChild.data][0]

            experiment_ref = interaction.getElementsByTagName('experimentRef')[0].childNodes[0].data    # type: ignore
        except (KeyError, IndexError, AttributeError) as e:
            logging.warning("Problem getting interactors from interaction: %s" % e)

        detection_method = ''
        publication = ''
        if experiment_ref in exp_dict and 'detection_method' in exp_dict[experiment_ref]:
            detection_method = exp_dict[experiment_ref]['detection_method']
        if experiment_ref in exp_dict and 'publication' in exp_dict[experiment_ref]:
            publication = exp_dict[experiment_ref]['publication']

        return [interactor1, self.ppi_edge_label, interactor2, self.ppi_ro_relation,
                publication, str(len(interactors)), interaction_type_str,
                detection_method]

    def interactor_to_node(self, interactor) -> List[Union[int, list]]:
        interactor_id = interactor.attributes['id'].value

        this_id = ''
        try:
            xrefs = interactor.getElementsByTagName('xref')
            pr = xrefs[0].getElementsByTagName('primaryRef')
            db = pr[0].attributes['db'].value

            prefix = ''
            if db in self.db_to_prefix:
                prefix = self.db_to_prefix[db]
            id_val = pr[0].attributes['id'].value

            # chebi ids (and only these) are already prepended with
            # prefix for some reason
            if db == 'chebi' and re.match('^CHEBI:', id_val):
                this_id = id_val
            else:
                this_id = ':'.join([prefix, id_val])

        except (KeyError, IndexError, AttributeError) as e:
            logging.warning(
                "Problem parsing id in xref interaction %s" % e)

        name = ''
        try:
            # xml parsing amirite
            name = interactor.getElementsByTagName('names')[0].getElementsByTagName(
                'shortLabel')[0].childNodes[0].data
        except (KeyError, IndexError, AttributeError) as e:
            logging.warning(
                "Problem parsing name in xref interaction %s" % e)

        category = 'biolink:Protein'
        try:
            type = \
            interactor.getElementsByTagName('interactorType')[0].getElementsByTagName(
                'shortLabel')[0].childNodes[0].data
            type = type.lower()
            if type in self.type_to_biolink_category:
                category = self.type_to_biolink_category[type]
        except (KeyError, IndexError, AttributeError) as e:
            logging.warning(
                "Problem parsing name in xref interaction %s" % e)

        return [interactor_id, [this_id, name, category]]

    def parse_experiment_info(self, xmldoc: object) -> Dict[int, str]:
        """Extract info about experiment from miXML doc

        :param self: IntAct instance
        :param xmldoc: a minidom object containing a miXML doc
        :return: dictionary with parsed info about experiments (publication, exp type)
        """
        exp_dict: dict = defaultdict(lambda: defaultdict(str))
        for experiment in xmldoc.getElementsByTagName('experimentDescription'):  # type: ignore
            if experiment.hasAttribute('id'):
                exp_id = experiment.getAttribute('id')
            else:
                continue

            # get pub data
            bibref = experiment.getElementsByTagName('bibref')
            if bibref and bibref[0].getElementsByTagName('primaryRef'):
                p_ref = bibref[0].getElementsByTagName('primaryRef')
                try:
                    db = p_ref[0].attributes['db'].value
                    this_id = p_ref[0].attributes['id'].value
                    if db in self.db_to_prefix:
                        db = self.db_to_prefix[db]
                    exp_dict[exp_id]['publication'] = ":".join([db, this_id])
                except (KeyError, IndexError, AttributeError):
                    pass

            # interaction detection method
            if experiment.getElementsByTagName('interactionDetectionMethod'):
                try:
                    method = experiment.getElementsByTagName(
                        'interactionDetectionMethod')
                    label = method[0].getElementsByTagName('shortLabel')[0].\
                        firstChild.data
                    exp_dict[exp_id]['detection_method'] = label
                except (KeyError, IndexError, AttributeError):
                    pass

        return exp_dict
