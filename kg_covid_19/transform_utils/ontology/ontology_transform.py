"""Transform an ontology in Obograph JSON format."""

import csv
import os
import uuid
from typing import Optional

from kgx.cli.cli_utils import transform  # type: ignore

from kg_covid_19.transform_utils.transform import Transform

ONTOLOGIES = {
    "HpTransform": "hp.json",
    "GoTransform": "go-plus.json",
    "MondoTransform": "mondo.json",
    "ChebiTransform": "chebi.json.gz",
}


class OntologyTransform(Transform):
    """Parse an Obograph JSON form of an Ontology into nodes and edges."""

    def __init__(self, input_dir: str = None, output_dir: str = None):
        """Initialize."""
        source_name = "ontologies"
        super().__init__(source_name, input_dir, output_dir)

    def run(self, data_file: Optional[str] = None) -> None:
        """Perform transformations to process an ontology.

        Args:
            data_file: data file to parse
        Returns:
            None.
        """
        if data_file:
            k = data_file.split(".")[0]
            data_file = os.path.join(self.input_base_dir, data_file)
            self.parse(k, data_file, k)
        else:
            # load all ontologies
            for k in ONTOLOGIES.keys():
                data_file = os.path.join(self.input_base_dir, ONTOLOGIES[k])
                self.parse(k, data_file, k)

    def parse(self, name: str, data_file: str, source: str) -> None:
        """Process the data_file.

        Args:
            name: Name of the ontology
            data_file: data file to parse
            source: Source name
        Returns:
             None.
        """
        print(f"Parsing {data_file}")
        compression: Optional[str]
        if data_file.endswith(".gz"):
            compression = "gz"
        else:
            compression = None

        transform(
            inputs=[data_file],
            input_format="obojson",
            input_compression=compression,
            output=os.path.join(self.output_dir, name),
            output_format="tsv",
        )

        # Extra step here to add extra nodes+edges for mappings
        if name == "chebi":
            edgefile_name = name + "_edges.tsv"
            nodefile_name = name + "_nodes.tsv"

            # Retrieve all node ids
            all_node_ids = []
            with open(os.path.join(self.output_dir, nodefile_name)) as nodefile:
                node_rows = csv.DictReader(nodefile, delimiter="\t")
                for row in node_rows:
                    all_node_ids.append(row["id"])
                all_node_ids = list(set(all_node_ids))

            # Get mappings for each node id
            node_mappings = {}
            with open("./maps/drugcentral-maps-kg_covid_19-0.1.sssom.tsv") as map_file:

                for _ in range(11):
                    next(map_file)
                norm_map = csv.DictReader(map_file, delimiter="\t")

                for row in norm_map:
                    if row["subject_id"] in all_node_ids and row["object_id"] != "":
                        node_mappings[row["subject_id"]] = row["object_id"]

            # For each node id with a mapping, build a new relation
            # and its corresponding nodes
            new_match_relations = []
            all_map_nodes = []
            for subject, object in node_mappings.items():
                urn = "urn:uuid:" + str(uuid.uuid1())
                new_relation = f"{urn}\t{subject}\tbiolink:exact_match\t{object}\tskos:exactMatch\tchebi.json.gz\n" # noqa: E501
                new_match_relations.append(new_relation)
                object_iri = (
                    "https://drugcentral.org/drugcard/" + (object.split(":"))[1]
                )
                new_map_node = (
                    f"{object}\tbiolink:Drug\t\t\t\t\t\t{object_iri}\t\t\t\t\t\t\t\n"
                )
                all_map_nodes.append(new_map_node)

            # Write all relations to the edge file
            with open(os.path.join(self.output_dir, edgefile_name), "a") as edgefile:
                for relation in new_match_relations:
                    edgefile.write(relation)

            # Write all mapped ids to the node file
            with open(os.path.join(self.output_dir, nodefile_name), "a") as nodefile:
                for node in all_map_nodes:
                    nodefile.write(node)
