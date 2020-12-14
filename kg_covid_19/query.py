import logging
import re

import yaml
from SPARQLWrapper import SPARQLWrapper, JSON, XML, TURTLE, N3, RDF, RDFXML, CSV, TSV  # type: ignore


def run_query(query: str, endpoint: str, return_format=JSON) -> dict:
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(return_format)
    results = sparql.query().convert()

    return results


def parse_query_rq(rq_file) -> dict:
    """

    Args:
        rq_file: sparql query in grlc rq format

    Returns: dict with parsed info about sparql query

    """
    parsed_rq = dict()
    with open(rq_file) as r:
        query = ''
        for line in r:
            if line.isspace():
                continue
            elif re.match('^\=\+ ', line):
                (key, value) = re.sub('^\=\+ ', '', line).rstrip().split(' ', maxsplit=1)
                parsed_rq[key] = value
            else:
                query += line
        parsed_rq['query'] = query
    return parsed_rq


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
