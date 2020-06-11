from SPARQLWrapper import SPARQLWrapper, JSON


def run_query(query: str, endpoint: str) \
        -> dict:  # for lack of a better way to type json
    sparql = SPARQLWrapper("http://kg-hub-rdf.berkeleybop.io/blazegraph/sparql")
    sparql.setQuery("""
      SELECT (COUNT(?v2) AS ?v1) ?v0 
      WHERE {
        ?v2 <https://w3id.org/biolink/vocab/category> ?v0
      } GROUP BY ?v0
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return results
