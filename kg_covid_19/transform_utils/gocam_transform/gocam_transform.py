import gzip
import os
import shutil
from typing import Optional

from kgx import RdfTransformer, PandasTransformer # type: ignore

from kg_covid_19.transform_utils.transform import Transform


class GocamTransform(Transform):
    """
    GocamTransform parses GO-CAMs that have been subjected to
    RDF edge project (REP) pattern.
    """
    def __init__(self, input_dir: str = None, output_dir: str = None):
        source_name = "GOCAMs"
        super().__init__(source_name, input_dir, output_dir)

    def run(self, data_file: Optional[str] = None, **kwargs) -> None:
        """Method is called and performs needed transformations to process
        an ontology.

        Args:
            data_file: data file to parse

        Returns:
            None.

        """
        if not data_file:
            data_file = os.path.join(self.input_base_dir, 'lifted-go-cams-20200619.xml.gz')

        if data_file.endswith('.gz'):
            print("Decompressing")
            decompressed_data_file = '.'.join(data_file.split('.')[0:-1])
            self.decompress_file(data_file, decompressed_data_file)
        else:
            decompressed_data_file = data_file

        if 'input_format' in kwargs:
            input_format = kwargs['input_format']
            if input_format not in {'nt', 'ttl', 'rdf/xml'}:
                raise ValueError(f"Unsupported input_format: {input_format}")
        else:
            input_format = None
        self.parse(decompressed_data_file, input_format)

    def parse(self, data_file: str, input_format: str) -> None:
        """Processes the data_file.

        Args:
            data_file: data file to parse
            input_format: format of input file

        Returns:
             None

        """
        # define prefix to IRI mappings
        cmap = {
            'REACT': 'http://purl.obolibrary.org/obo/go/extensions/reacto.owl#REACTO_',
            'WB': 'http://identifiers.org/wormbase/',
            'FB': 'http://identifiers.org/flybase/',
            'LEGO': 'http://geneontology.org/lego/',
            'GOCAM': 'http://model.geneontology.org/',
            'TAIR.LOCUS': 'http://identifiers.org/tair.locus/',
            'POMBASE': 'http://identifiers.org/PomBase',
            'DICTYBASE.GENE': 'http://identifiers.org/dictybase.gene/',
            'XENBASE': 'http://identifiers.org/xenbase/'
        }

        # define predicates that are to be treated as node properties
        np = {
            'http://geneontology.org/lego/evidence',
            'https://w3id.org/biolink/vocab/subjectActivity',
            'https://w3id.org/biolink/vocab/objectActivity',
        }

        print(f"Parsing {data_file}")
        transformer = RdfTransformer(curie_map=cmap)
        transformer.parse(data_file, node_property_predicates=np, input_format=input_format)
        output_transformer = PandasTransformer(transformer.graph)
        output_transformer.save(os.path.join(self.output_dir, self.source_name), output_format='tsv', mode=None)

    def decompress_file(self, input_file: str, output_file: str):
        """Decompress a file.

        Args:
             input_file: Input file
             output_file: Output file

        Returns:
            str

        """
        FH = gzip.open(input_file, 'rb')
        WH = open(output_file, 'wb')
        WH.write(FH.read())
        return output_file
