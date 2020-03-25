import gzip
import os
from typing import Dict, List

from kg_emerging_viruses.transform_utils.transform import Transform
from kg_emerging_viruses.utils.transform_utils import write_node_edge_item, get_item_by_priority


"""
Ingest protein-protein interactions from STRING DB.

Dataset location: https://string-db.org/cgi/download.pl
GitHub Issue: https://github.com/kg-emerging-viruses/kg-emerging-viruses/issues/10


Write node and edge headers that look something like:

Node: 
id  name    category
protein:1234    TBX4    Protein 

Edge: 
subject edge_label  object  relation
protein:1234    interacts_with  protein:4567    RO:0002434
"""

MAPPING_FILE_URL = 'https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz'

class StringTransform(Transform):
    """
    TODO: flexible input_dir and output_dor
    TODO: map protein identifiers to gene identifiers
    TODO: add protein to gene edges
    """
    def __init__(self):
        super().__init__(source_name="STRING")

    # def load_mapping(self, input_dir: str, output_dir: str, species_id: List):
    #     pass
    #
    # def download_mapping(self, url: str, output_dir):
    #     outfile = f"{output_dir}/gene_info.gz"
    #     encode_download(url=url, path=outfile)

    def run(self) -> None:
        """Method is called and performs needed transformations to process
        protein-protein interactions from the STRING DB data."""
        interactions_file = os.path.join(self.input_base_dir, "9606.protein.links.full.v11.0.txt.gz")
        os.makedirs(self.output_dir, exist_ok=True)
        protein_node_type = "biolink:Protein"
        edge_label = "biolink:interacts_with"
        edge_core_header = ['subject', 'edge_label', 'object', 'relation', 'combined_score']
        edge_additional_headers = [
            'neighborhood', 'neighborhood_transferred', 'fusion', 'cooccurence',
            'homology', 'coexpression', 'coexpression_transferred', 'experiments',
            'experiments_transferred', 'database', 'database_transferred', 'textmining',
            'textmining_transferred'
        ]
        self.edge_header = edge_core_header + edge_additional_headers
        relation = 'RO:0002434'
        seen = []

        with open(self.output_node_file, 'w') as node, \
                open(self.output_edge_file, 'w') as edge, \
                gzip.open(interactions_file, 'rt') as interactions:

            node.write("\t".join(self.node_header) + "\n")
            edge.write("\t".join(self.edge_header) + "\n")

            header_items = parse_header(interactions.readline())
            for line in interactions:
                items_dict = parse_stringdb_interactions(line, header_items)
                protein1 = get_item_by_priority(items_dict, ['protein1'])
                protein1 = '.'.join(protein1.split('.')[1:])
                protein1 = f"ENSEMBL:{protein1}"
                #gene1 = get_gene_for_protein(protein1)
                #protein_to_gene_map[protein1] = gene1
                protein2 = get_item_by_priority(items_dict, ['protein2'])
                protein2 = '.'.join(protein2.split('.')[1:])
                protein2 = f"ENSEMBL:{protein2}"
                #gene2 = get_gene_for_protein(protein2)
                #protein_to_gene_map[protein2] = gene2

                # write node data
                if protein1 not in seen:
                    write_node_edge_item(
                        fh=node,
                        header=self.node_header,
                        data=[protein1, "", protein_node_type]
                    )

                if protein2 not in seen:
                    write_node_edge_item(
                        fh=node,
                        header=self.node_header,
                        data=[protein2, "", protein_node_type]
                    )
                seen.append(protein1)
                seen.append(protein2)

                # write edge data
                edge_data = [protein1, edge_label, protein2, relation, items_dict['combined_score']]
                for x in edge_additional_headers:
                    edge_data.append(items_dict[x] if x in items_dict else "")

                write_node_edge_item(
                    fh=edge,
                    header=self.edge_header,
                    data=edge_data
                )


def parse_stringdb_interactions(this_line: str, header_items: List) -> Dict:
    """Methods processes a line of text from Drug Central.

    Args:
        this_line: A string containing a line of text.
        header_items: A list of header items.

    Returns:
        item_dict: A dictionary of header items and a processed Drug Central string.
    """

    items = this_line.strip().split(" ")
    item_dict = dict(zip(header_items, items))
    return item_dict


def parse_header(header_string: str, sep: str = ' ') -> List:
    """Parses header data.

    Args:
        header_string: A string containing header items.
        sep: A string containing a delimiter.

    Returns:
        A list of header items.
    """

    header = header_string.strip().split(sep)

    return [i.replace('"', '') for i in header]
