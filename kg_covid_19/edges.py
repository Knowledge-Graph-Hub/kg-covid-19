import pandas as pd


def make_edges(num_edges: int, nodes: str, edges: str, output_dir: str,
               train_fraction: float, validation: bool, node_types: list,
               min_degree: int) -> None:
    """Prepare positive and negative edges for testing and training

    Args:
        :param num_edges      number of positive and negative edges to emit
        :param nodes     nodes of input graph, in KGX TSV format [data/merged/nodes.tsv]
        :param edges:   edges for input graph, in KGX TSV format [data/merged/edges.tsv]
        :param output_dir:     directory to output edges and new graph [data/edges/]
        :param train_fraction: fraction of edges to emit as training [0.8]
        :param validation:     should we make validation edges? [False]
        :param min_degree      when choosing edges, what is the minimum degree of nodes
                        involved in the edge [1]
        :param node_types:    what node types should we make edges from? by default, any
                        type. If specified, should use items from 'category' column
    Returns:
        None.
        :param min_degree:

    """
    pass


def tsv_to_df(tsv_file: str) -> pd.DataFrame:
    """Read in a TSV file and return a pandas dataframe

    :param tsv_file: file to read in
    :return: pandas dataframe
    """
    df = pd.read_csv(tsv_file, sep="\t")
    return df
