from ensmallen_graph import EnsmallenGraph
import tarfile
import compress_json

tar = tarfile.open("kg-covid-19.tar.gz")

tar.extractall()
graph = EnsmallenGraph.from_csv(
    edge_path="merged-kg_edges.tsv",
    sources_column="subject",
    destinations_column="object",
    directed=False,
    edge_types_column="edge_label",
    default_edge_type="biolink:association",
    node_path="merged-kg_nodes.tsv",
    nodes_column="id",
    node_types_column="category",
    default_node_type="biolink:NamedThing",
    ignore_duplicated_edges=True,
    ignore_duplicated_nodes=True,
    force_conversion_to_undirected=True
)

json_report = graph.report()
compress_json.dump(json_report, "kg-covid-19-ensmallen-report.json")

