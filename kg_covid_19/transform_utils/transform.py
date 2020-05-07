import os
from typing import Optional


class Transform:
    """Parent class for transforms, that sets up a lot of default file info
    """

    DEFAULT_INPUT_DIR = os.path.join('data', 'raw')
    DEFAULT_OUTPUT_DIR = os.path.join('data', 'transformed')

    def __init__(self, source_name, input_dir: str = None, output_dir: str = None):
        # default columns, can be appended to or overwritten as necessary
        self.source_name = source_name
        self.node_header = ['id', 'name', 'category']
        self.edge_header = ['subject', 'edge_label', 'object', 'relation',
                            'provided_by']

        # default dirs
        self.input_base_dir = input_dir if input_dir else self.DEFAULT_INPUT_DIR
        self.output_base_dir = output_dir if output_dir else self.DEFAULT_OUTPUT_DIR
        self.output_dir = os.path.join(self.output_base_dir, source_name)
        os.makedirs(self.output_dir, exist_ok=True)

        # default filenames
        self.output_node_file = os.path.join(self.output_dir, "nodes.tsv")
        self.output_edge_file = os.path.join(self.output_dir, "edges.tsv")
        self.output_json_file = os.path.join(self.output_dir, "nodes_edges.json")

    def run(self, data_file: Optional[str] = None):
        pass
