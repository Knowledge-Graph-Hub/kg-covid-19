import json
import os
import uuid
from typing import List, Dict, Any, Set
from zipfile import ZipFile
import pandas as pd # type: ignore
from prefixcommons import contract_uri # type: ignore

from kg_covid_19.transform_utils.transform import Transform
from kg_covid_19.utils import write_node_edge_item


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

    def run(self, data_files: List = None) -> None:
        """Method is called and performs needed transformations to process
        annotations from SciBite CORD-19

        Args:
            data_files: data files to parse

        Returns:
            None.

        """
        if not data_files:
            data_files = list()
            data_files.append(os.path.join(self.input_base_dir, "CORD-19_1_2.zip"))
            data_files.append(os.path.join(self.input_base_dir, "cv19_scc.zip"))

        self.node_header = ['id', 'name', 'category', 'description']
        self.edge_header = ['subject', 'edge_label', 'object', 'relation', 'provided_by']
        node_handle = open(self.output_node_file, 'w')
        edge_handle = open(self.output_edge_file, 'w')
        node_handle.write("\t".join(self.node_header) + "\n")
        edge_handle.write("\t".join(self.edge_header) + "\n")
        self.parse_annotations(node_handle, edge_handle, data_files[0])
        self.parse_cooccurrence(node_handle, edge_handle, data_files[1])

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
            data_dir = os.path.join(self.input_base_dir, 'data', subset, subset)
            for filename in os.listdir(data_dir):
                file = os.path.join(data_dir, filename)
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
        paper_id = doc['paper_id']
        metadata = doc['metadata']
        abstract = doc['abstract']
        body_text = doc['body_text']
        terms = set()
        provided_by = f"{self.source_name}"
        if subset:
            provided_by += f" {subset}"
        # extract hits from metadata
        terms.update(self.extract_termite_hits(metadata))
        # extract hits from abstract
        for x in abstract:
            terms.update(self.extract_termite_hits(x))
        # extract hits from body text
        for x in body_text:
            terms.update(self.extract_termite_hits(x))

        # add a biolink:Publication for each paper
        write_node_edge_item(
            fh=node_handle,
            header=self.node_header,
            data=[
                f"CORD:{paper_id}",
                f"{metadata['title']}",
                "biolink:Publication",
                ""
            ]
        )
        self.seen.add(paper_id)

        # TODO: use CURIE for terms
        for t in terms:
            if t not in self.seen:
                # add a biolink:OntologyClass node for each term
                write_node_edge_item(
                    fh=node_handle,
                    header=self.node_header,
                    data=[
                        f"{t}",
                        f"{self.concept_name_map[t]}",
                        "biolink:OntologyClass" if len(t) != 2 else "biolink:NamedThing",
                        ""
                    ]
                )
                self.seen.add(t)

            # add has_annotation edge between OntologyClass and Publication
            write_node_edge_item(
                fh=edge_handle,
                header=self.edge_header,
                data=[
                    f"{t}",
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
                if t not in self.seen:
                    # add a biolink:OntologyClass node for each term
                    write_node_edge_item(
                        fh=node_handle,
                        header=self.node_header,
                        data=[
                            f"{t}",
                            self.concept_name_map[t] if t in self.concept_name_map else "",
                            "biolink:OntologyClass" if len(t) != 2 else "biolink:NamedThing",
                            ""
                        ]
                    )
                    self.seen.add(t)

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
                # add has_member edges between co-occurrence entity and each term
                write_node_edge_item(
                    fh=edge_handle,
                    header=self.edge_header,
                    data=[
                        f"{information_entity}",
                        "biolink:related_to",
                        f"{t}",
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








