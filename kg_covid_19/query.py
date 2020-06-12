import logging

import yaml
from SPARQLWrapper import SPARQLWrapper, JSON, XML, TURTLE, N3, RDF, RDFXML, CSV, TSV  # type: ignore


def run_query(query: str, endpoint: str, return_format=JSON) -> dict:
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(return_format)
    results = sparql.query().convert()

    return results


def parse_query_yaml(yaml_file) -> dict:
    return yaml.load(open(yaml_file))


def result_dict_to_tsv(result_dict: dict, outfile: str) -> None:
    with open(outfile, 'wt') as f:
        # header
        f.write("\t".join(result_dict['head']['vars']) + "\n")
        for row in result_dict['results']['bindings']:
            row_items = []
            for col in result_dict['head']['vars']:
                try:
                    row_items.append(row[col]['value'])
                except KeyError:
                    logging.error('Problem retrieving result for col %s in row %s' %
                                  (col, "\t".join(row)))
                    row_items.append('ERROR')
            try:
                f.write("\t".join(row_items) + "\n")
            except:
                pass
