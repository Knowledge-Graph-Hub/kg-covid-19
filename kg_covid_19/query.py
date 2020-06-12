import yaml
from SPARQLWrapper import SPARQLWrapper, JSON, XML, TURTLE, N3, RDF, RDFXML, CSV, TSV


def run_query(query: str, endpoint: str, return_format=JSON) \
        -> dict:  # for lack of a better way to type json
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(return_format)
    results = sparql.query().convert()

    return results


def parse_query_yaml(yaml_file) -> dict:
    return yaml.load(open(yaml_file))

