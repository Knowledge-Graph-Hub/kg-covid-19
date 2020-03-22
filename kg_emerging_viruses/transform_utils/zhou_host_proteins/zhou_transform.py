import os
from tabula import io
from kg_emerging_viruses.utils.transform_utils import multi_page_table_to_list,\
    write_node_edge_item

"""
Ingest Covid-19 associated host proteins from Suppl Fig 3 of this paper: 
https://www.nature.com/articles/s41421-020-0153-3

https://github.com/kg-emerging-viruses/kg-emerging-viruses/issues/2

Write node and edge headers that look something like:

Node: 
id  name    category
gene:1234   TBX4    Gene 

Edge: 

subject edge_label  object   relation
gene:1234  contributes_to_condition    MONDO:0005002   RO:0003304
"""

# TODO: refactor zhou_transform so that it accepts input.
def zhou_transform():
    node_header = ['id', 'name', 'category']
    edge_header = ['subject', 'edge_label', 'object', 'relation', 'publications']

    source_name = "zhou_host_proteins"
    input_file = os.path.join("data", "raw", "41421_2020_153_MOESM1_ESM.pdf")
    output_base_dir = os.path.join("data", "transformed", source_name)

    pubmed_curie_prefix = "PMID:"
    gene_curie_prefix = "NCBI:"
    publication_node_type = "Biolink:Publication"
    gene_node_type = 'Biolink:Gene'
    virus_node_type = 'Biolink:OrganismalEntity'

    # list of RO interactions:
    # https://raw.githubusercontent.com/oborel/obo-relations/master/subsets/ro-interaction.owl
    host_gene_vgene_edge_label = 'biotically interacts with'
    host_gene_vgene_relation = 'RO:0002437'

    NCBITaxon_curie_prefix = 'NCBITaxon:'
    corona_info = {
        'IBV':        {'taxon_id': 11120},
        'MHV':        {'taxon_id': 502104},
        'HCoV-NL63':  {'taxon_id': 277944},
        'HCoV-229E':  {'taxon_id': 11137},
        'SARS':       {'taxon_id': 227859},
        'MERS':       {'taxon_id': 1335626},
    }

    # for tsv output:
    output_node_file = os.path.join(output_base_dir, "nodes.tsv")
    output_edge_file = os.path.join(output_base_dir, "edges.tsv")

    # for json output
    json_output_file = os.path.join(output_base_dir, "nodes_edges.json")

    # make directory in data/transformed
    output_dir = os.path.join(output_base_dir)
    os.makedirs(output_dir, exist_ok=True)

    fig_3_table_unformatted = io.read_pdf(input_file,
                                          output_format='json',
                                          pages=[5, 6, 7],
                                          multiple_tables=True)

    fig_3_table = multi_page_table_to_list(fig_3_table_unformatted)

    with open(output_node_file, 'w') as node, open(output_edge_file, 'w') as edge:

        # write node.tsv header
        node.write("\t".join(node_header) + "\n")
        edge.write("\t".join(edge_header) + "\n")

        for row in fig_3_table:

            if row['Coronavirus'] not in corona_info:
                raise Exception("Can't find info for coronavirus {}", row['Coronavirus'])
            this_corona_info = corona_info[row['Coronavirus']]
            corona_curie = NCBITaxon_curie_prefix + str(this_corona_info['taxon_id'])

            #
            # write nodes
            #
            # virus
            write_node_edge_item(fh=node, header=node_header,
                                 data=[gene_curie_prefix + row['Host Gene ID'],
                                       row['Host Protein'],
                                       gene_node_type])

            # host gene
            write_node_edge_item(fh=node, header=node_header,
                                 data=[corona_curie,
                                       row['Coronavirus'],
                                       virus_node_type])

            #
            # write edge
            #
            write_node_edge_item(fh=edge, header=edge_header,
                                 data=[
                                       gene_curie_prefix + row['Host Gene ID'],
                                       host_gene_vgene_edge_label,
                                       corona_curie,
                                       host_gene_vgene_relation,
                                       pubmed_curie_prefix + row['PubMed ID']
            ])




