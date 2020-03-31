#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

import obonet  # type: ignore
from typing.io import TextIO  # type: ignore

from kg_covid_19.transform_utils.transform import Transform
from kg_covid_19.utils import write_node_edge_item
from kg_covid_19.utils.transform_utils import get_item_by_priority, data_to_dict, \
    ItemInDictNotFound

"""Ingest Human Phenotype Ontology (no annotations for now, just the ontology)

Dataset location: https://raw.githubusercontent.com/obophenotype/human-phenotype-ontology/master/hp.obo
GitHub Issue: https://github.com/Knowledge-Graph-Hub/kg-covid-19/issues/48

"""


class HpoTransform(Transform):

    def __init__(self):
        super().__init__(source_name="hpo")

    def run(self):
        self.node_header.extend(["comments", "description"])
        hpo_node_type = "biolink:PhenotypicFeature"
        hpo_edge_label = "rdfs:subClassOf"
        hpo_ro_relation = "RO:0002351"
        hpo_obo_file = os.path.join(self.input_base_dir, "hp.obo")

        # make directory in data/transformed
        os.makedirs(self.output_dir, exist_ok=True)

        # transform data, something like:
        with open(self.output_node_file, 'w') as node, \
             open(self.output_edge_file, 'w') as edge:

            # write headers (change default node/edge headers if necessary
            node.write("\t".join(self.node_header) + "\n")
            edge.write("\t".join(self.edge_header) + "\n")

            graph = obonet.read_obo(hpo_obo_file)

            for id_, data in graph.nodes(data=True):

                # Write HPO nodes
                self.write_hpo_node(node, id_, data, hpo_node_type)

                # if we see is_a relationship(s), write parent-child edge(s)
                if 'is_a' in data:
                    for parent in data['is_a']:
                        self.write_hpo_edge(edge,
                                            id_,
                                            hpo_edge_label,
                                            parent,
                                            hpo_ro_relation)


    def write_hpo_node(self, fh: TextIO, id: str, data: dict, node_type: str) -> None:
        # Try to get comments/def in case this is useful for ML
        try:
            comment_field = get_item_by_priority(data, ['comment'])
        except ItemInDictNotFound:
            comment_field = ""

        try:
            description = get_item_by_priority(data, ['def'])
        except ItemInDictNotFound:
            description = ""

        try:
            name_field = get_item_by_priority(data, ['name'])
        except ItemInDictNotFound:
            name_field = ""

        write_node_edge_item(fh=fh, header=self.node_header,
                             data=[id,
                                   name_field,
                                   node_type,
                                   comment_field,
                                   description
                                   ])

    def write_hpo_edge(self,
                       fh: TextIO,
                       subject: str,
                       edge_label: str,
                       object: str,
                       relation: str) -> None:

        # ['subject', 'edge_label', 'object', 'relation', 'publications']
        write_node_edge_item(fh=fh, header=self.edge_header,
                             data=[subject,
                                   edge_label,
                                   object,
                                   relation,
                                   ""])
