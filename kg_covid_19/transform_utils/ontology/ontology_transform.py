import os

from typing import Optional

from kgx.cli.cli_utils import transform  # type: ignore
from kg_covid_19.transform_utils.transform import Transform

ONTOLOGIES = {
    'HpTransform': 'hp.json',
    'GoTransform': 'go-plus.json',
    'MondoTransform':  'mondo.json',
    'ChebiTransform': 'chebi.json.gz'
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
            self.parse(k, data_file, k)
        else:
            # load all ontologies
            for k in ONTOLOGIES.keys():
                data_file = os.path.join(self.input_base_dir, ONTOLOGIES[k])
                self.parse(k, data_file, k)

    def parse(self, name: str, data_file: str, source: str) -> None:
        """Processes the data_file.
        Args:
            name: Name of the ontology
            data_file: data file to parse
            source: Source name
        Returns:
             None.
        """
        print(f"Parsing {data_file}")
        compression: Optional[str]
        if data_file.endswith('.gz'):
            compression = 'gz'
        else:
            compression = None

        transform(inputs=[data_file],
                  input_format='obojson',
                  input_compression=compression,
                  output=os.path.join(self.output_dir, name),
                  output_format='tsv')
