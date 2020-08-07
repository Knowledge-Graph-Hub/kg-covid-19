import gzip
import logging
import os
import compress_json  # type: ignore
from typing import Dict, List, Any, Set, Optional, IO

from kg_covid_19.transform_utils.transform import Transform
from kg_covid_19.utils.transform_utils import write_node_edge_item, \
    get_item_by_priority, uniprot_make_name_to_id_mapping, collapse_uniprot_curie

"""
Ingest protein-protein interactions from STRING DB.

Dataset location: https://string-db.org/cgi/download.pl
GitHub Issue: https://github.com/kg-emerging-viruses/kg-emerging-viruses/issues/10


Write node and edge headers that look something like:

Node: 
id  name    category    xrefs   provided_by
protein:1234    TBX4    biolink:Protein UniProtKB:123456    STRING 

xrefs contains the UniProtKB id for the protein, if available

Edge: 
subject edge_label  object  relation
protein:1234    interacts_with  protein:4567    RO:0002434


"""

NCBI_FTP_URL = 'https://ftp.ncbi.nlm.nih.gov/gene/DATA/'
PROTEIN_MAPPING_FILE = 'gene2ensembl.gz'
GENE_INFO_FILE = 'gene_info.gz'

# make name to id map for uniprot names of human proteins
UNIPROT_ID_MAPPING = "HUMAN_9606_idmapping.dat.gz"


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
        logging.info("Loading Ensembl Gene to Protein mapping")
        self.load_mapping(self.input_base_dir, self.output_dir, ['9606'])
        logging.info("Load mappings from NCBI gene_info")
        self.load_gene_info(self.input_base_dir, self.output_dir, ['9606'])

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
                    self.gene_info_map[ncbi_gene_identifier] = {
                        'ENSEMBL': ensembl_gene_identifier}
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
                    self.gene_info_map[ncbi_gene_identifier] = {
                        'symbol': symbol, 'description': description}
                else:
                    self.gene_info_map[ncbi_gene_identifier]['symbol'] = symbol
                    self.gene_info_map[ncbi_gene_identifier]['description'] = description

    def run(self, data_file: Optional[str] = None) -> None:
        """Method is called and performs needed transformations to process
        protein-protein interactions from the STRING DB data.

        Args:
            data_file: data file to parse

        Returns:
            None.

        """
        if not data_file:
            data_file = os.path.join(
                self.input_base_dir,
                "9606.protein.links.full.v11.0.txt.gz"
            )
        os.makedirs(self.output_dir, exist_ok=True)
        protein_node_type = "biolink:Protein"
        edge_label = "biolink:interacts_with"
        self.node_header = compress_json.local_load("node_header.json")
        edge_core_header = compress_json.local_load("edge_core_header.json")
        edge_additional_headers = compress_json.local_load(
            "edge_additional_headers.json")

        self.edge_header = edge_core_header + edge_additional_headers
        relation = 'RO:0002434'
        seen_proteins: Set = set()
        seen_genes: Set = set()

        # Required to align the node edge header of the gene
        # with the default header
        self.extra_header = [""]*(len(edge_additional_headers)+1)

        # make string ENSP to Uniprot id mapping dict
        string_to_uniprot_id_map = uniprot_make_name_to_id_mapping(
            os.path.join(self.input_base_dir, UNIPROT_ID_MAPPING))

        with open(self.output_node_file, 'w') as node, \
                open(self.output_edge_file, 'w') as edge, \
                gzip.open(data_file, 'rt') as interactions:

            node.write("\t".join(self.node_header) + "\n")
            edge.write("\t".join(self.edge_header) + "\n")

            header_items = parse_header(interactions.readline())
            for line in interactions:
                items_dict = parse_stringdb_interactions(line, header_items)
                proteins = []
                for protein_name in ('protein1', 'protein2'):
                    nat_string_id = get_item_by_priority(items_dict, [protein_name])
                    protein = '.'.join(nat_string_id.split('.')[1:])
                    proteins.append(protein)

                    if protein in self.protein_gene_map:
                        gene = self.protein_gene_map[protein]
                        if gene not in seen_genes:
                            seen_genes.add(gene)
                            ensemble_gene = f"ENSEMBL:{gene}"
                            gene_informations=self.gene_info_map[self.ensembl2ncbi_map[gene]]
                            write_node_edge_item(
                                fh=node,
                                header=self.node_header,
                                data=[
                                    ensemble_gene,
                                    gene_informations['symbol'],
                                    'biolink:Gene',
                                    gene_informations['description'],
                                    f"NCBIGene:{self.ensembl2ncbi_map[gene]}",
                                    self.source_name
                                ]
                            )
                            write_node_edge_item(
                                fh=edge,
                                header=self.edge_header,
                                data=[
                                    ensemble_gene,
                                    "biolink:has_gene_product",
                                    f"ENSEMBL:{protein}",
                                    "RO:0002205",
                                    "NCBI",
                                    ""
                                ] + self.extra_header
                            )

                    # write node data
                    if protein not in seen_proteins:
                        seen_proteins.add(protein)

                        # if we have an equivalent Uniprot ID for this Ensembl protein
                        # ID make an xref edge, and a node for the Uniprot ID
                        uniprot_curie = ''
                        if protein in string_to_uniprot_id_map:
                            uniprot_curie = \
                                f"UniProtKB:{string_to_uniprot_id_map[protein]}"
                            uniprot_curie = collapse_uniprot_curie(uniprot_curie)

                        write_node_edge_item(
                            fh=node,
                            header=self.node_header,
                            data=[f"ENSEMBL:{protein}", "",
                                  protein_node_type,
                                  "",
                                  uniprot_curie,  # xref
                                  self.source_name
                                  ]
                        )


                # write edge data
                write_node_edge_item(
                    fh=edge,
                    header=self.edge_header,
                    data=[
                             f"ENSEMBL:{proteins[0]}",
                             edge_label,
                             f"ENSEMBL:{proteins[1]}",
                             relation,
                             "STRING",
                             "biolink:Association",
                             items_dict['combined_score']
                         ] + [items_dict.get(header, "") for header in edge_additional_headers]
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

