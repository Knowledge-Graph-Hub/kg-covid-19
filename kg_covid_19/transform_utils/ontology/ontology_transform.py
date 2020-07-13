import os
import logging
import tempfile
from typing import Optional

from kg_covid_19.transform_utils.transform import Transform
from kgx import PandasTransformer, ObographJsonTransformer, RdfOwlTransformer  # type: ignore

from kg_covid_19.utils.transform_utils import ungzip_to_tempdir

ONTOLOGIES = {
    'HpTransform': 'hp.json',
    'GoTransform': 'go-plus.json',
    'MondoTransform':  'mondo.json',
    'GoCam': 'go-cams.rdf.gz'
}


class OntologyTransform(Transform):
    """
    OntologyTransform parses an Obograph JSON form of an Ontology into nodes nad edges.
    """
    def __init__(self, input_dir: str = None, output_dir: str = None):
        source_name = "ontologies"
        super().__init__(source_name, input_dir, output_dir)

    def run(self, data_file: Optional[str] = None, input_format = 'json') -> None:
        """Method is called and performs needed transformations to process
        an ontology.

        Args:
            data_file: data file to parse

        Returns:
            None.

        """
        if data_file:
            k = data_file.split('.')[0]

            if data_file.endswith('.gz'):
                input_format = 'rdf/xml'
                xml_tempdir = tempfile.mkdtemp()
                data_file = ungzip_to_tempdir(os.path.join(
                    self.input_base_dir, data_file), xml_tempdir)

            data_file = os.path.join(self.input_base_dir, data_file)
            self.parse(k, data_file, k,  input_format=input_format)
        else:
            # load all ontologies
            for k in ONTOLOGIES.keys():

                data_file = os.path.join(self.input_base_dir, ONTOLOGIES[k])

                if data_file.endswith('.gz'):
                    input_format = 'rdf/xml'
                    xml_tempdir = tempfile.mkdtemp()
                    data_file = ungzip_to_tempdir(os.path.join(
                        self.input_base_dir, data_file), xml_tempdir)

                self.parse(k, data_file, k, input_format=input_format)

    def parse(self, name: str, data_file: str, source: str,
              input_format: str = 'json') -> None:
        """Processes the data_file.

        Args:
            name: Name of the ontology
            data_file: data file to parse
            source: source name
            input_format: format of input file

        Returns:
             None.

        """
        logging.info(f"Parsing {data_file}")
        if input_format == 'json':
            transformer = ObographJsonTransformer()
        elif input_format == 'rdf/xml':
            transformer = RdfOwlTransformer()
        else:
            raise ValueError("No way to parse format %s" % format)
        transformer.parse(data_file, provided_by=source)
        output_transformer = PandasTransformer(transformer.graph)
        output_transformer.save(filename=os.path.join(self.output_dir, f'{name}'), output_format='tsv', mode=None)
