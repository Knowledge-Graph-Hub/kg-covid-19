import os
import logging
from typing import Optional

from kg_covid_19.transform_utils.transform import Transform
from kgx import PandasTransformer, ObographJsonTransformer # type: ignore

ONTOLOGIES = {
    'HpTransform': 'hp.json',
    'GoTransform': 'go-plus.json',
    'MondoTransform':  'mondo.json'
}

class OntologyTransform(Transform):
    """
    OntologyTransform parses an Obograph JSON form of an Ontology into nodes nad edges.
    """
    def __init__(self, input_dir: str = None, output_dir: str = None):
        source_name = "ontologies"
        super().__init__(source_name, input_dir, output_dir)

    def run(self, data_file: Optional[str] = None) -> None:
        """Method is called and performs needed transformations to process
        an ontology.

        Args:
            data_file: data file to parse

        Returns:
            None.

        """
        if data_file:
            k = data_file.split('.')[0]
            data_file = os.path.join(self.input_base_dir, data_file)
            self.parse(k, data_file)
        else:
            # load all ontologies
            for k in ONTOLOGIES.keys():
                data_file = os.path.join(self.input_base_dir, ONTOLOGIES[k])
                self.parse(k, data_file)

    def parse(self, name: str, data_file: str) -> None:
        """Processes the data_file.

        Args:
            name: Name of the ontology
            data_file: data file to parse

        Returns:
             None.

        """
        logging.info(f"Parsing {data_file}")
        transformer = ObographJsonTransformer()
        transformer.parse(data_file)
        output_transformer = PandasTransformer(transformer.graph)
        output_transformer.save(filename=os.path.join(self.output_dir, f'{name}'), extension='tsv', mode=None)
