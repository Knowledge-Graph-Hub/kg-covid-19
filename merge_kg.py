import os
import logging
import argparse
import yaml

from kgx import Transformer, NeoTransformer
from kgx.cli.utils import get_file_types, get_transformer

parser = argparse.ArgumentParser(description='A script that uses KGX to merge one or more sources to create a KG, driven by a config YAML.')
parser.add_argument('--yaml',  help='the YAML file', required=True)
args = parser.parse_args()


# parse config YAML
with open(args.yaml, 'r') as YML:
    cfg = yaml.load(YML, Loader=yaml.FullLoader)


transformers = []
for key in cfg['target']:
    target = cfg['target'][key]
    logging.info("Loading {}".format(key))
    if target['type'] in get_file_types():
        # loading from a file
        transformer = get_transformer(target['type'])()
        for f in target['filename']:
            transformer.parse(f, input_format='tsv')
        transformers.append(transformer)
    elif target['type'] == 'neo4j':
        transformer = NeoTransformer(None, target['uri'], target['username'],  target['password'])
        transformer.load()
        transformers.append(transformer)
    else:
        logging.error("type {} not yet supported".format(target['type']))

merged_transformer = Transformer()
merged_transformer.merge_graphs([x.graph for x in transformers])
print(merged_transformer.graph.nodes(data=True))
print(merged_transformer.graph.edges(data=True))

destination = cfg['destination']
if destination['type'] in ['csv', 'tsv', 'ttl', 'json', 'tar']:
    destination_transformer = get_transformer(destination['type'])()
    destination_transformer.save(destination['filename'], extension=destination['type'])
elif destination['type'] == 'neo4j':
    destination_transformer = NeoTransformer(merged_transformer.graph, uri=destination['uri'], username=destination['username'], password=destination['password'])
    destination_transformer.save_with_unwind()
else:
    logging.error("type {} not yet supported for KGX load-and-merge operation.".format(destination['type']))
