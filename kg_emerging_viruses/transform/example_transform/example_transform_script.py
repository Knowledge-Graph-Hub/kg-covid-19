import os

"""
Example script to transform downloaded data into a graph format that KGX can
ingest directly, in either TSV or JSON format:
https://github.com/NCATS-Tangerine/kgx/blob/master/data-preparation.md

Input: any file in data/raw/ (that was downloaded by placing a URL in incoming.txt/yaml
and running `run.py download`

Output: transformed data in data/raw/[source name]:

Either TSV, output these two files:
nodes.tsv
edges.tsv

Or JSON, all in one file:
nodes_edges.json
"""

source_name = "example"
input_file = os.path.join("data", "raw", "example_data.csv")  # must exist already
output_base_dir = os.path.join("data", "transformed")

# for tsv output:
output_node_file = os.path.join(output_base_dir, "nodes.tsv")
output_edge_file = os.path.join(output_base_dir, "edges.tsv")

# for json output
json_output_file = os.path.join(output_base_dir, "nodes_edges.json")

# make directory in data/transformed
output_dir = os.path.join(output_base_dir, source_name)
os.mkdir(output_dir)

# replace with downloaded data of for this source

# transform data, something like:
# with open(input_file, 'r') as f,\
#     open(output_node_file, 'w') as node,\
#     open(output_edge_file, 'w') as edge:
#     for line in f:
#        # transform
#        output_node_file.write(this_node1)
#        output_node_file.write(this_node2)
#        output_edge_file.write(this_edge)
