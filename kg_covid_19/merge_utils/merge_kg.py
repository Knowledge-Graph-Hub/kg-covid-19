import logging
import os
from typing import Dict, List
import yaml
import networkx as nx
from kgx import NeoTransformer
from kgx.cli.utils import get_file_types, get_transformer
from kgx.operations.graph_merge import merge_all_graphs
from kgx.operations.summarize_graph import generate_graph_stats


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
            if target['type'] in {'tsv', 'neo4j'}:
                if 'filters' in target:
                    filters = target['filters']
                    node_filters = filters['node_filters'] if 'node_filters' in filters else {}
                    edge_filters = filters['edge_filters'] if 'edge_filters' in filters else {}
                    for k, v in node_filters.items():
                        transformer.set_node_filter(k, set(v))
                    for k, v in edge_filters.items():
                        transformer.set_edge_filter(k, set(v))
                    logging.info(f"with node filters: {node_filters}")
                    logging.info(f"with edge filters: {edge_filters}")
            for f in target['filename']:
                transformer.parse(f, input_format='tsv')
                transformer.graph.name = key
            transformers.append(transformer)
        elif target['type'] == 'neo4j':
            transformer = NeoTransformer(None, target['uri'], target['username'],  target['password'])
            transformer.load()
            transformers.append(transformer)
            transformer.graph.name = key
        else:
            logging.error("type {} not yet supported".format(target['type']))
        stats_filename = f"{key}_stats.yaml"
        generate_graph_stats(transformer.graph, key, stats_filename)

    # merge all subgraphs into a single graph
    merged_graph = merge_all_graphs([x.graph for x in transformers])
    merged_graph.name = 'merged_graph'
    generate_graph_stats(merged_graph, merged_graph.name, f"merged_graph_stats.yaml")

    # write the merged graph
    if 'destination' in config:
        for _, destination in config['destination'].items():
            if destination['type'] == 'neo4j':
                destination_transformer = NeoTransformer(
                    merged_graph,
                    uri=destination['uri'],
                    username=destination['username'],
                    password=destination['password']
                )
                destination_transformer.save_with_unwind()
            elif destination['type'] in get_file_types():
                destination_transformer = get_transformer(destination['type'])(merged_graph)
                destination_transformer.save(destination['filename'], extension=destination['type'])
            else:
                logging.error("type {} not yet supported for KGX load-and-merge operation.".format(destination['type']))

    return merged_graph
