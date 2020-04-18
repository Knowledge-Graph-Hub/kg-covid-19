#!/usr/bin/env python
# -*- coding: utf-8 -*-
import fnmatch
import logging
import os
import tempfile
from os import unlink
from typing import IO

from kg_covid_19.transform_utils.transform import Transform
from kg_covid_19.utils.transform_utils import write_node_edge_item, unzip_to_tempdir
from xml.dom import minidom

"""
Ingest IntAct protein/protein interaction data 
https://www.ebi.ac.uk/intact/
specifically about coronavirus viral protein/host protein interactions. 

The file at this URL:
https://t.co/OUGKWbpQHG?amp=1
is zip file containing XML files that describe coronavirus interactions shown in a
publication. 

Each XML looks like this: 
<entrySet>
<entry>
    <source></source> <!-- stuff about IntAct -->
    <experimentList>
        <bibref>
           <xref>
           <primaryRef db="pubmed" dbAc="MI:0446" id="14647384" >  <!-- pubmed ID to cite on edge -->
           </xref>
        </bibref>
    </experimentList>
    <interactorList>
        <interactor id="3674850">  <!-- interactor id, used in interactionList below -->
            <names>
            <shortLabel>ace2_human</shortLabel>       <!-- name for protein -->
            <xref>
            <primaryRef db="uniprotkb" dbAc="MI:0486" id="Q9BYF1">  <!-- db:id is CURIE for protein (Uniprot sometimes, but not always) -->
        ...
    </interactorList>
    <interactionList>
        <interaction>
            <primaryRef db="intact" dbAc="MI:0469" id="EBI-25487299" > <!-- db:id is a CURIE for interaction -->
            
            <interactionType>
                <names>
                <shortLabel>physical association</shortLabel>
                <fullName>physical association</fullName>            
                <primaryRef db="psi-mi" dbAc="MI:0488" id="MI:0915" refType="identity" refTypeAc="MI:0356"/> <!-- type of association -->
            <interactorRef>3674850</interactorRef>  <!-- reference to interactor id above -->
            
    </interactionList>
</entry>
</entrySet>
"""


class IntAct(Transform):

    def __init__(self, input_dir: str = None, output_dir: str = None) -> None:
        source_name = "intact"
        super().__init__(source_name, input_dir, output_dir)
        # interactor type to biolink category
        self.type_to_biolink_category = {
            'protein': 'biolink:Protein',
            'rna': 'biolink:RNA'
        }

    def run(self) -> None:
        """Method to run transform to ingest data from IntAct for viral/human PPIs"""

        zip_file = os.path.join(self.input_base_dir, 'intact_coronavirus.zip')

        pubmed_curie_prefix = 'PMID:'
        publication_node_type = 'biolink:Publication'
        protein_node_type = 'biolink:Protein'

        # list of RO interactions:
        # https://raw.githubusercontent.com/oborel/obo-relations/master/subsets/ro-interaction.owl
        host_gene_vgene_edge_label = 'biolink:interacts_with'
        host_gene_vgene_relation = 'RO:0002437'

        ncbitaxon_curie_prefix = 'NCBITaxon:'

        # for tsv output:
        output_node_file = os.path.join(self.output_dir, 'nodes.tsv')
        output_edge_file = os.path.join(self.output_dir, 'edges.tsv')

        # make directory in data/transformed
        os.makedirs(self.output_dir, exist_ok=True)

        with open(output_node_file, 'w') as node,\
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

                nodes_edges = self.parse_xml_to_nodes_edges(os.path.join(file_path, file))
                # TODO: write out nodes and edges

                # write out nodes
                for this_node in nodes_edges['nodes']:
                    write_node_edge_item(fh=node,
                                         header=self.node_header,
                                         data=this_node)

    def parse_xml_to_nodes_edges(self, xml_file: str) -> dict:
        parsed = dict()
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

        for key, value in nodes_dict.items():
            parsed['nodes'].append(value)


        # edges

        return parsed

    def interactor_to_node(self, interactor) -> [int, list]:
        interactor_id = interactor.attributes['id'].value

        this_id = ''
        try:
            xrefs = interactor.getElementsByTagName('xref')
            pr = xrefs[0].getElementsByTagName('primaryRef')
            this_id = ':'.join([pr[0].attributes['db'].value,
                                pr[0].attributes['id'].value])
        except (KeyError, IndexError) as e:
            logging.warning("Problem parsing id in xref interaction % " % interactor.toxml())

        name = ''
        try:
            # xml parsing amirite
            name = interactor.getElementsByTagName('names')[0].getElementsByTagName('shortLabel')[0].childNodes[0].data
        except (KeyError, IndexError) as e:
            logging.warning("Problem parsing name in xref interaction % " % interactor.toxml())

        category = 'biolink:Protein'
        try:
            type = interactor.getElementsByTagName('interactorType')[0].getElementsByTagName('shortLabel')[0].childNodes[0].data
            type = type.lower()
            if type in self.type_to_biolink_category:
                category = self.type_to_biolink_category[type]
        except (KeyError, IndexError) as e:
            logging.warning("Problem parsing name in xref interaction % " % interactor.toxml())

        return [interactor_id, [this_id, name, category]]
