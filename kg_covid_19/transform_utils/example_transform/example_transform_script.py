#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
from typing import Optional

from kg_covid_19.transform_utils.transform import Transform

"""
Example script to transform downloaded data into a graph format that KGX can ingest directly, in either TSV or JSON 
format: https://github.com/NCATS-Tangerine/kgx/blob/master/data-preparation.md

Input: any file in data/raw/ (that was downloaded by placing a URL in incoming.txt/yaml and running `run.py download`
Output: transformed data in data/raw/[source name]:

Output these two files:
- nodes.tsv
- edges.tsv
"""


class YourTransform(Transform):

    def __init__(self, input_dir: str = None, output_dir: str = None):
        source_name = "some_unique_name"
        super().__init__(source_name, input_dir, output_dir)

    def run(self, data_file: Optional[str] = None):
        # replace with downloaded data of for this source
        input_file = os.path.join(
            self.input_base_dir, "example_data.csv")  # must exist already

        # make directory in data/transformed
        os.makedirs(self.output_dir, exist_ok=True)

        # transform data, something like:
        with open(input_file, 'r') as f, \
                open(self.output_node_file, 'w') as node, \
                open(self.output_edge_file, 'w') as edge:

            # write headers (change default node/edge headers if necessary
            node.write("\t".join(self.node_header) + "\n")
            edge.write("\t".join(self.edge_header) + "\n")

            # transform data, something like:
            for line in f:
                pass
                # transform line into nodes and edges
                # node.write(this_node1)
                # node.write(this_node2)
                # edge.write(this_edge)
