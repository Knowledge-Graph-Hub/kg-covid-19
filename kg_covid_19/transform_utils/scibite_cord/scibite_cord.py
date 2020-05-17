import gzip
import json
import os
import re
import uuid
from typing import List, Dict, Any, Set, Optional
from zipfile import ZipFile
import pandas as pd # type: ignore
from prefixcommons import contract_uri # type: ignore

from kg_covid_19.transform_utils.transform import Transform
from kg_covid_19.utils import write_node_edge_item

CUSTOM_CMAP = {
    'CHEMBL.COMPOUND': 'https://www.ebi.ac.uk/chembl/compound_report_card/',
    'MESH': 'https://id.nlm.nih.gov/mesh/',
    'UniProtKB': 'https://www.uniprot.org/uniprot/',
    'HGNC': 'http://www.genenames.org/cgi-bin/gene_symbol_report?match='
}

class ScibiteCordTransform(Transform):
    """
    ScibiteCordTransform parses the SciBite annotations on CORD-19 dataset
    to extract concept to publication annotations and co-occurrences.
    """
    def __init__(self, input_dir: str = None, output_dir: str = None):
        source_name = "SciBite-CORD-19"
        super().__init__(source_name, input_dir, output_dir)
        self.concept_name_map: Dict = {}
        self.seen: Set = set()
        self.gene_info_map: Dict = {}
        self.load_gene_info(self.input_base_dir, self.output_dir, ['9606'])

    def run(self, data_file: Optional[str] = None) -> None:
        """Method is called and performs needed transformations to process
        annotations from SciBite CORD-19

        Args:
            data_file: data file to parse

        Returns:
            None.

        """
        data_files = list()
        if not data_file:
            data_files.append(os.path.join(self.input_base_dir, "CORD-19_1_4.zip"))
            data_files.append(os.path.join(self.input_base_dir, "cv19_scc_1_2.zip"))
        else:
            data_files.append(data_file)

        self.node_header = ['id', 'name', 'category', 'description']
        self.edge_header = ['subject', 'edge_label', 'object', 'relation', 'provided_by']
        node_handle = open(self.output_node_file, 'w')
        edge_handle = open(self.output_edge_file, 'w')
        node_handle.write("\t".join(self.node_header) + "\n")
        edge_handle.write("\t".join(self.edge_header) + "\n")
        self.parse_annotations(node_handle, edge_handle, data_files[0])
        #self.parse_cooccurrence(node_handle, edge_handle, data_files[1])

    def parse_annotations(self, node_handle: Any, edge_handle: Any, data_file: str) -> None:
        """Parse annotations from CORD-19_1_2.zip.

        Args:
            node_handle: File handle for nodes.csv.
            edge_handle: File handle for edges.csv.
            data_file: Path to CORD-19_1_2.zip.

        Returns:
             None.

        """
        with ZipFile(data_file, 'r') as ZF:
            ZF.extractall(path=self.input_base_dir)

        subsets = ['biorxiv_medrxiv', 'comm_use_subset', 'noncomm_use_subset', 'custom_license']
        for subset in subsets:
            subset_dir = os.path.join(self.input_base_dir, 'CORD19', subset, subset)
            for data_dir in os.listdir(subset_dir):
                if os.path.isdir(os.path.join(subset_dir, data_dir)):
                    for filename in os.listdir(os.path.join(subset_dir, data_dir)):
                        file = os.path.join(subset_dir, data_dir, filename)
                        doc = json.load(open(file))
                        self.parse_annotation_doc(node_handle, edge_handle, doc, subset)


    def parse_annotation_doc(self, node_handle, edge_handle, doc: Dict, subset: str = None) -> None:
        """Parse a JSON document corresponding to a publication.

        Args:
            node_handle: File handle for nodes.csv.
            edge_handle: File handle for edges.csv.
            doc: JSON document as dict.
            subset: The subset name for this dataset.

        Returns:
            None.

        """
        terms = set()
        paper_id = doc['paper_id']
        title = None
        if 'metadata' in doc:
            metadata = doc['metadata']
            title = metadata['title'].replace('\n', ' ')
            # extract hits from metadata
            terms.update(self.extract_termite_hits(metadata))

        if 'abstract' in doc:
            abstract = doc['abstract']
            # extract hits from abstract
            for x in abstract:
                terms.update(self.extract_termite_hits(x))

        if 'body_text' in doc:
            body_text = doc['body_text']
            # extract hits from body text
            for x in body_text:
                terms.update(self.extract_termite_hits(x))

        provided_by = f"{self.source_name}"
        if subset:
            provided_by += f" {subset}"

        # add a biolink:Publication for each paper
        write_node_edge_item(
            fh=node_handle,
            header=self.node_header,
            data=[
                f"CORD:{paper_id}",
                f"{title}",
                "biolink:Publication",
                ""
            ]
        )
        self.seen.add(paper_id)

        for t in terms:
            curie = self.contract_uri(t)
            if t not in self.seen:
                # add a biolink:OntologyClass node for each term
                write_node_edge_item(
                    fh=node_handle,
                    header=self.node_header,
                    data=[
                        f"{curie}",
                        f"{self.concept_name_map[t]}",
                        "biolink:OntologyClass" if len(t) != 2 else "biolink:NamedThing",
                        ""
                    ]
                )
                self.seen.add(curie)

            # add has_annotation edge between OntologyClass and Publication
            write_node_edge_item(
                fh=edge_handle,
                header=self.edge_header,
                data=[
                    f"{curie}",
                    f"biolink:related_to",
                    f"CORD:{paper_id}",
                    "SIO:000255",
                    provided_by
                ]
            )

    def parse_cooccurrence(self, node_handle: Any, edge_handle: Any, data_file: str) -> None:
        """Parse term co-occurrences from cv19_scc.zip.

        Args:
            node_handle: File handle for nodes.csv.
            edge_handle: File handle for edges.csv.
            data_file: Path to cv19_scc.zip.

        Returns:
             None.

        """
        with ZipFile(data_file, 'r') as ZF:
            ZF.extractall(path=self.input_base_dir)

        df = pd.read_csv(os.path.join(self.input_base_dir, 'cv19_scc.tsv'), delimiter='\t', encoding='utf-8')
        for index, row in df.iterrows():
            self.parse_cooccurrence_record(node_handle, edge_handle, row)

    def parse_cooccurrence_record(self, node_handle: Any, edge_handle: Any, record: Dict) -> None:
        """Parse term-cooccurrences.

        Args:
            node_handle: File handle for nodes.csv.
            edge_handle: File handle for edges.csv.
            record: A dictionary corresponding to a row from a table.

        Returns:
             None.

        """
        terms = set()
        paper_id = record['document_id']
        if not pd.isna(record['entity_uris']):
            terms.update(record['entity_uris'].split('|'))
            # add a biolink:Publication for each paper
            if paper_id not in self.seen:
                write_node_edge_item(
                    fh=node_handle,
                    header=self.node_header,
                    data=[
                        f"CORD:{paper_id}",
                        "",
                        "biolink:Publication",
                        ""
                    ]
                )
                self.seen.add(paper_id)

            for t in terms:
                curie = self.contract_uri(t)
                if t not in self.seen:
                    # add a biolink:OntologyClass node for each term
                    write_node_edge_item(
                        fh=node_handle,
                        header=self.node_header,
                        data=[
                            f"{curie}",
                            self.concept_name_map[t] if t in self.concept_name_map else "",
                            "biolink:OntologyClass" if len(t) != 2 else "biolink:NamedThing",
                            ""
                        ]
                    )
                    self.seen.add(curie)

            information_entity = uuid.uuid1()
            write_node_edge_item(
                fh=node_handle,
                header=self.node_header,
                data=[
                    f"{uuid.uuid1()}",
                    "",
                    "biolink:InformationContentEntity",
                    ""
                ]
            )
            # add has_annotation edge between co-occurrence entity and publication
            write_node_edge_item(
                fh=edge_handle,
                header=self.edge_header,
                data=[
                    f"{information_entity}",
                    "biolink:related_to",
                    f"{record['document_id']}",
                    "SIO:000255", # 'has annotation'
                    f"{self.source_name}"
                ]
            )
            for t in terms:
                curie = self.contract_uri(t)
                # add has_member edges between co-occurrence entity and each term
                write_node_edge_item(
                    fh=edge_handle,
                    header=self.edge_header,
                    data=[
                        f"{information_entity}",
                        "biolink:related_to",
                        f"{curie}",
                        f"SIO:000059", # 'has member'
                        f"{self.source_name}"
                    ]
                )

    def extract_termite_hits(self, data: Dict) -> Set:
        """Parse term-cooccurrences.

        Args:
            node_handle: File handle for nodes.csv.
            edge_handle: File handle for edges.csv.
            data: A dictionary.

        Returns:
             None.

        """
        terms = set()
        termite_hits = data['termite_hits']
        for k, v in termite_hits.items():
            for hit in v:
                terms.update([hit['id']])
                if hit['id'] not in self.concept_name_map:
                    self.concept_name_map[hit['id']] = hit['name']
        return terms

    def contract_uri(self, iri) -> str:
        """Contract a given IRI.

        Contract a given IRI, with special parsing and transformations
        depending on the nature of the IRI.

        Args:
            iri: IRI as string

        Returns:
            str.

        """
        curie = ""
        if 'http://www.genenames.org/cgi-bin/gene_symbol_report?match=' in iri:
            identifier = iri.split('=')[-1]
            if identifier in self.gene_info_map:
                curie = f"NCBIGene:{self.gene_info_map[identifier]['NCBI']}"
            else:
                [curie] = contract_uri(iri, cmaps=[CUSTOM_CMAP])
        else:
            if self.is_iri(iri):
                curie = contract_uri(iri)
                if curie:
                    curie = curie[0]
                else:
                    curie = contract_uri(iri, cmaps=[CUSTOM_CMAP])
                    if curie:
                        curie = curie[0]
                    else:
                        curie = iri
            elif self.is_curie(iri):
                curie = iri
            else:
                curie = f":{iri}"

        return curie

    @staticmethod
    def is_curie(s: str) -> bool:
        """Check if a given string is a CURIE.

        Args:
            s: string

        Returns:
            bool.

        """
        m = re.match(r"^[^ :]+:[^/ :]+$", s)
        return bool(m)

    @staticmethod
    def is_iri(s) -> bool:
        """Check ig a given string is an IRI.

        Args:
            s: string

        Returns:
            bool.

        """
        m = re.match(r"^http[s]?://", s)
        return bool(m)

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
        file_path = os.path.join(self.input_base_dir, 'gene_info.gz')

        with gzip.open(file_path, 'rt') as FH:
            for line in FH:
                records = line.split('\t')
                if records[0] not in species_id:
                    continue
                ncbi_gene_identifier = records[1]
                symbol = records[2]
                hgnc_identifier = self.get_identifier_by_prefix(records[5], 'HGNC:')
                description = records[8]
                if symbol not in self.gene_info_map:
                    self.gene_info_map[symbol] = {
                        'symbol': symbol,
                        'description': description,
                        'NCBI': ncbi_gene_identifier,
                        'HGNC': hgnc_identifier
                    }

    @staticmethod
    def get_identifier_by_prefix(record, prefix):
        """Get identifier from a list based on prefix.

        Args:
            record: record from NCBI gene_info.
            prefix: prefix of the identifier to extract.

        Returns:
            str

        """
        identifier = None
        element = record.split('|')
        identifier = [x for x in element if prefix in x]
        if identifier:
            identifier = identifier[0]
            if 'HGNC:HGNC:' in identifier:
                identifier = ':'.join(identifier.split(':')[1:])
        return identifier








