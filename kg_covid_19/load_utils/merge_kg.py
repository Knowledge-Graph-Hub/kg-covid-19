import logging
import os
from typing import Dict, List
import yaml
import networkx as nx
from kgx import Transformer, NeoTransformer
from kgx.cli.utils import get_file_types, get_transformer
from kgx.operations.graph_merge import GraphMerge

def parse_load_config(yaml_file: str) -> Dict:
    """Parse load config YAML.

    Args:
        yaml_file: A string pointing to a KGX compatible config YAML.

    Returns:
        Dict: The config as a dictionary.

    """
    with open(yaml_file) as YML:
        config = yaml.load(YML, Loader=yaml.FullLoader)
    return config


def load_and_merge(yaml_file: str) -> nx.MultiDiGraph:
    """Load and merge sources defined in the config YAML.

    Args:
        yaml_file: A string pointing to a KGX compatible config YAML.

    Returns:
        networkx.MultiDiGraph: The merged graph.

    """
    gm = GraphMerge()
    config = parse_load_config(yaml_file)
    transformers: List = []

    # make sure all files exist before we start load
    for key in config['target']:
        target = config['target'][key]
        logging.info("Checking that file exist for {}".format(key))
        if target['type'] in get_file_types():
            for f in target['filename']:
                if not os.path.exists(f) or not os.path.isfile(f):
                    raise FileNotFoundError("File {} for transform {}  in yaml file {} "
                                            "doesn't exist! Dying.", f, key, yaml_file)

    # read all the sources defined in the YAML
    for key in config['target']:
        target = config['target'][key]
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

    # merge all subgraphs into a single graph
    merged_graph = gm.merge_all_graphs([x.graph for x in transformers])

    # write the merged graph
    if 'destination' in config:
        destination = config['destination']
        if destination['type'] in ['csv', 'tsv', 'ttl', 'json', 'tar']:
            destination_transformer = get_transformer(destination['type'])(merged_graph)
            destination_transformer.save(destination['filename'], extension=destination['type'])
        elif destination['type'] == 'neo4j':
            destination_transformer = NeoTransformer(
                merged_graph,
                uri=destination['uri'],
                username=destination['username'],
                password=destination['password']
            )
            destination_transformer.save_with_unwind()
        else:
            logging.error("type {} not yet supported for KGX load-and-merge operation.".format(destination['type']))

    return merged_graph
