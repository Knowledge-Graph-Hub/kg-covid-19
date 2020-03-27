import os


class Transform:
    """Parent class for transforms, that sets up a lot of default file info
    """

    def __init__(self, source_name):
        # default columns, can be appended to or overwritten as necessary
        self.source_name = source_name
        self.node_header = ['id', 'name', 'category']
        self.edge_header = ['subject', 'edge_label', 'object', 'relation',
                            'publications']

        # default dirs
        self.output_base_dir = os.path.join("data", "transformed")
        self.input_base_dir = os.path.join("data", "raw")
        self.output_dir = os.path.join(self.output_base_dir, source_name)

        # default filenames
        self.output_node_file = os.path.join(self.output_dir, "nodes.tsv")
        self.output_edge_file = os.path.join(self.output_dir, "edges.tsv")
        self.output_json_file = os.path.join(self.output_dir, "nodes_edges.json")


