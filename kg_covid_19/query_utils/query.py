class Query:
    def __init__(self, query_name: str, input_dir: str, output_dir: str) -> None:
        self.query_name = query_name
        self.input_dir = input_dir
        self.output_dir = output_dir

    def run(self, input_dir: str, output_dir: str) -> None:
        pass
