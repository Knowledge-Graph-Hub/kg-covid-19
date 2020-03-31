import gzip
import os
from typing import Dict, List, Any

from kg_covid_19.transform_utils.transform import Transform
from kg_covid_19.utils.transform_utils import write_node_edge_item, get_item_by_priority

from encodeproject import download as encode_download  # type: ignore

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

NCBI_FTP_URL = 'https://ftp.ncbi.nlm.nih.gov/gene/DATA/'
PROTEIN_MAPPING_FILE = 'gene2ensembl.gz'
GENE_INFO_FILE = 'gene_info.gz'

class StringTransform(Transform):
    """
    StringTransform parses interactions from STRING DB into nodes and edges.
    """
    def __init__(self, input_dir: str = None, output_dir: str = None):
        source_name = "STRING"
        super().__init__(source_name, input_dir, output_dir)

        self.protein_gene_map: Dict[str, Any] = {}
        self.gene_info_map: Dict[str, Any] = {}
        self.ensembl2ncbi_map: Dict[str, Any] = {}
        self.load_mapping(self.input_base_dir, output_dir, ['9606'])
        self.load_gene_info(self.input_base_dir, output_dir, ['9606'])


    def load_mapping(self, input_dir: str, output_dir: str, species_id: List = None) -> None:
        """Load Ensembl Gene to Protein mapping from NCBI gene2ensembl (gene2ensembl.gz).

        Args:
            input_dir: A string pointing to the directory to import data from.
            output_dir: A string pointing to the directory to output data to.
            species_id: A list with the species IDs.

        Returns:
            None.

        """
        if not species_id:
            # default to just human
            species_id = ['9606']
        file_path = os.path.join(input_dir, PROTEIN_MAPPING_FILE)
        with gzip.open(file_path, 'rt') as FH:
            for line in FH:
                records = line.split('\t')
                if records[0] not in species_id:
                    continue
                ncbi_gene_identifier = records[1]
                ensembl_gene_identifier = records[2]
                ensembl_protein_identifier = records[6].split('.')[0]
                if ensembl_protein_identifier not in self.protein_gene_map:
                    self.protein_gene_map[ensembl_protein_identifier] = ensembl_gene_identifier
                if ncbi_gene_identifier not in self.gene_info_map:
                    self.gene_info_map[ncbi_gene_identifier] = {'ENSEMBL': ensembl_gene_identifier}
                if ensembl_gene_identifier not in self.ensembl2ncbi_map:
                    self.ensembl2ncbi_map[ensembl_gene_identifier] = ncbi_gene_identifier

    def load_gene_info(self, input_dir: str, output_dir: str, species_id: List = None) -> None:
        """Load mappings from NCBI gene_info (gene_info.gz).

        Args:
            input_dir: A string pointing to the directory to import data from.
            output_dir: A string pointing to the directory to output data to.
            species_id: A list with the species IDs.

        Returns:
            None.

        """
        if not species_id:
            # default to just human
            species_id = ['9606']
        file_path = os.path.join(self.input_base_dir, GENE_INFO_FILE)

        with gzip.open(file_path, 'rt') as FH:
            for line in FH:
                records = line.split('\t')
                if records[0] not in species_id:
                    continue
                ncbi_gene_identifier = records[1]
                symbol = records[2]
                description = records[8]
                if ncbi_gene_identifier not in self.gene_info_map:
                    self.gene_info_map[ncbi_gene_identifier] = {'symbol': symbol, 'description': description}
                else:
                    self.gene_info_map[ncbi_gene_identifier]['symbol'] = symbol
                    self.gene_info_map[ncbi_gene_identifier]['description'] = description

    def run(self, data_file: str = None) -> None:
        """Method is called and performs needed transformations to process
        protein-protein interactions from the STRING DB data.

        Args:
            data_file: data file to parse

        Returns:
            None.

        """
        if not data_file:
            data_file = os.path.join(self.input_base_dir, "9606.protein.links.full.v11.0.txt.gz")
        os.makedirs(self.output_dir, exist_ok=True)
        protein_node_type = "biolink:Protein"
        edge_label = "biolink:interacts_with"
        self.node_header = ['id', 'name', 'category', 'description', 'alias']
        edge_core_header = ['subject', 'edge_label', 'object', 'relation', 'provided_by', 'combined_score']
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
                gzip.open(data_file, 'rt') as interactions:

            node.write("\t".join(self.node_header) + "\n")
            edge.write("\t".join(self.edge_header) + "\n")

            header_items = parse_header(interactions.readline())
            for line in interactions:
                items_dict = parse_stringdb_interactions(line, header_items)
                protein1 = get_item_by_priority(items_dict, ['protein1'])
                protein1 = '.'.join(protein1.split('.')[1:])
                if protein1 in self.protein_gene_map:
                    gene1 = self.protein_gene_map[protein1]
                else:
                    gene1 = None
                protein2 = get_item_by_priority(items_dict, ['protein2'])
                protein2 = '.'.join(protein2.split('.')[1:])
                if protein2 in self.protein_gene_map:
                    gene2 = self.protein_gene_map[protein2]
                else:
                    gene2 = None

                if gene1 and gene1 not in seen:
                    write_node_edge_item(
                        fh=node,
                        header=self.node_header,
                        data=[
                            f"ENSEMBL:{gene1}",
                            self.gene_info_map[self.ensembl2ncbi_map[gene1]]['symbol'],
                            'biolink:Gene',
                            self.gene_info_map[self.ensembl2ncbi_map[gene1]]['description'],
                            f"NCBIGene:{self.ensembl2ncbi_map[gene1]}"
                        ]
                    )
                    write_node_edge_item(
                        fh=edge,
                        header=self.edge_header,
                        data=[
                            f"ENSEMBL:{gene1}",
                            "biolink:has_gene_product",
                            protein1,
                            "RO:0002205",
                            "NCBI",
                            ""
                        ] + ["" for x in edge_additional_headers]
                    )
                    seen.append(gene1)

                if gene2 and gene2 not in seen:
                    write_node_edge_item(
                        fh=node,
                        header=self.node_header,
                        data=[
                            f"ENSEMBL:{gene2}",
                            self.gene_info_map[self.ensembl2ncbi_map[gene2]]['symbol'],
                            'biolink:Gene',
                            self.gene_info_map[self.ensembl2ncbi_map[gene2]]['description'],
                            f"NCBIGene:{self.ensembl2ncbi_map[gene2]}"
                        ]
                    )
                    write_node_edge_item(
                        fh=edge,
                        header=self.edge_header,
                        data=[
                            f"ENSEMBL:{gene2}",
                            "biolink:has_gene_product",
                            protein2,
                            "RO:0002205",
                            "NCBI",
                            ""
                        ] + ["" for x in edge_additional_headers]
                    )
                    seen.append(gene2)

                # write node data
                if protein1 not in seen:
                    write_node_edge_item(
                        fh=node,
                        header=self.node_header,
                        data=[f"ENSEMBL:{protein1}", "", protein_node_type, "", ""]
                    )

                if protein2 not in seen:
                    write_node_edge_item(
                        fh=node,
                        header=self.node_header,
                        data=[f"ENSEMBL:{protein2}", "", protein_node_type, "", ""]
                    )
                seen.append(protein1)
                seen.append(protein2)

                # write edge data
                edge_data = [protein1, edge_label, protein2, relation, "STRING", items_dict['combined_score']]
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
