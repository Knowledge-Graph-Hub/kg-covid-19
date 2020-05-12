import logging

from kg_covid_19.query_utils.target_candidates.target_candidates \
    import TargetCandidates

QUERIES = {
    'TargetCandidates': TargetCandidates
}


def run_query(query: str, output_dir: str) -> None:
    logging.info(f"Running query {query}")
    t = QUERIES[query](output_dir)
    t.run()
