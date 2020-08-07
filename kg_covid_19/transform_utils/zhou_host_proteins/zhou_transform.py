#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
from typing import Optional

from tabula import io  # type: ignore

from kg_covid_19.transform_utils.transform import Transform
from kg_covid_19.utils.transform_utils import multi_page_table_to_list, write_node_edge_item

"""
Ingest Covid-19 associated host proteins from Suppl Fig 3 of this paper: 
https://www.nature.com/articles/s41421-020-0153-3

GitHub Issue: https://github.com/kg-emerging-viruses/kg-emerging-viruses/issues/2


Write node and edge headers that look something like:

Node: 
id  name    category
gene:1234   TBX4    Gene 

Edge: 
subject edge_label  object   relation
gene:1234  contributes_to_condition    MONDO:0005002   RO:0003304
"""


class ZhouTransform(Transform):

    def __init__(self, input_dir: str = None, output_dir: str = None) -> None:
        source_name = "zhou_host_proteins"
        super().__init__(source_name, input_dir, output_dir)
        self.node_header = ['id', 'name', 'category', 'provided_by']
        self.edge_header = ['subject', 'edge_label', 'object', 'relation',
                            'provided_by', 'type', 'publication']

    def run(self, data_file: Optional[str] = None):
        """Method is called and performs needed transformations to process the zhou host protein data, additional
        information on this data can be found in the comment at the top of this script."""

        input_file = os.path.join(self.input_base_dir, '41421_2020_153_MOESM1_ESM.pdf')

        pubmed_curie_prefix = 'PMID:'
        gene_curie_prefix = 'NCBIGene:'
        publication_node_type = 'biolink:Publication'
        gene_node_type = 'biolink:Gene'
        virus_node_type = 'biolink:OrganismalEntity'

        # list of RO interactions:
        # https://raw.githubusercontent.com/oborel/obo-relations/master/subsets/ro-interaction.owl
        host_gene_vgene_edge_label = 'biolink:interacts_with'
        host_gene_vgene_relation = 'RO:0002437'

        ncbitaxon_curie_prefix = 'NCBITaxon:'
        corona_info = {
            'IBV': {'taxon_id': 11120},
            'MHV': {'taxon_id': 502104},
            'HCoV-NL63': {'taxon_id': 277944},
            'HCoV-229E': {'taxon_id': 11137},
            'SARS': {'taxon_id': 227859},
            'MERS': {'taxon_id': 1335626},
        }

        # for tsv output:
        output_node_file = os.path.join(self.output_dir, 'nodes.tsv')
        output_edge_file = os.path.join(self.output_dir, 'edges.tsv')

        # make directory in data/transformed
        os.makedirs(self.output_dir, exist_ok=True)

        fig_3_table_unformatted = io.read_pdf(input_file,
                                              output_format='json',
                                              pages=[5, 6, 7],
                                              multiple_tables=True)

        fig_3_table = multi_page_table_to_list(fig_3_table_unformatted)

        with open(output_node_file, 'w') as node, open(output_edge_file, 'w') as edge:

            # write node.tsv header
            node.write('\t'.join(self.node_header) + '\n')
            edge.write('\t'.join(self.edge_header) + '\n')

            for row in fig_3_table:

                if row['Coronavirus'] not in corona_info:
                    raise Exception("Can't find info for coronavirus {}", row['Coronavirus'])

                this_corona_info = corona_info[row['Coronavirus']]
                corona_curie = ncbitaxon_curie_prefix + str(this_corona_info['taxon_id'])

                # WRITE NODES
                # virus
                write_node_edge_item(fh=node, header=self.node_header,
                                     data=[gene_curie_prefix + row['Host Gene ID'],
                                           row['Host Protein'],
                                           gene_node_type,
                                           self.source_name])

                # host gene
                write_node_edge_item(fh=node, header=self.node_header,
                                     data=[corona_curie,
                                           row['Coronavirus'],
                                           virus_node_type,
                                           self.source_name])

                # WRITE EDGES
                write_node_edge_item(fh=edge, header=self.edge_header,
                                     data=[
                                         gene_curie_prefix + row['Host Gene ID'],
                                         host_gene_vgene_edge_label,
                                         corona_curie,
                                         host_gene_vgene_relation,
                                         self.source_name,
                                         'biolink:Association',
                                         pubmed_curie_prefix + row['PubMed ID']
                                     ])

        return None
