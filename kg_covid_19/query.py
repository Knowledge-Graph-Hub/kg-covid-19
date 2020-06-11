import logging

QUERIES = {
    'TargetCandidates': ''
}


def run_query(query: str, input_dir: str, output_dir: str) -> None:
    logging.info(f"Running query {query}")
    t = QUERIES[query](input_dir, output_dir)
    t.run()
