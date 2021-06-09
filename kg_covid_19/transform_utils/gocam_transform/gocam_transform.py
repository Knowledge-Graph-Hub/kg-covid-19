import gzip
import os
from typing import Optional, Dict

from kgx.cli.cli_utils import prepare_output_args, prepare_input_args
from kgx.transformer import Transformer  # type: ignore
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
            data_file = os.path.join(self.input_base_dir, 'lifted-go-cams-20200619.nt')

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
            input_format = 'nt'
        self.parse(decompressed_data_file, input_format, compression=None)

    def parse(self, data_file: str, input_format: str,
              compression: Optional[str] = None) -> None:
        """Processes the data_file.

        Args:
            data_file: data file to parse
            input_format: format of input file
            compression: compression

        Returns:
             None

        """
        print(f"Parsing {data_file}")

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

        source: Dict = {
            'input': {
                'format': input_format,
                'compression': compression,
                'filename': data_file,
            },
            'output': {
                'format': 'tsv',
                'compression': None,
                'filename': os.path.join(self.output_dir, self.source_name),
            },
        }
        input_args = prepare_input_args(
            key=self.source_name,
            source=source,
            output_directory=os.path.join(self.output_dir, self.source_name),
            prefix_map=cmap,
            node_property_predicates=np,
            predicate_mappings=None
        )
        output_args = prepare_output_args(
            key=self.source_name,
            source=source,
            output_directory=os.path.join(self.output_dir, self.source_name),
            reverse_prefix_map=None,
            reverse_predicate_mappings=None,
            property_types=None,
        )
        transformer = Transformer(stream=False)
        input_args['filename'] = [input_args['filename']]
        transformer.transform(input_args, output_args)
        # input_args = {
        #     'format': input_format,
        #     # 'compression': compression,
        #     'prefix_map': cmap,
        #     'node_property_predicates': np
        # }
        #
        # output_args = {
        #     'format': 'tsv',
        #     'filename': os.path.join(self.output_dir, self.source_name)
        # }
        # this is how this is done in the cli transform() method:
        # key = self.source_name  # I guess
        # source: Dict = {
        #             'input': {
        #                 'format': input_format,
        #                 'compression': compression,
        #                 'filename': data_file
        #             },
        #             'output': {
        #                 'format': 'tsv',
        #                 'compression': None,
        #                 'filename': os.path.join(self.output_dir, self.source_name),
        #             },
        # }
        #
        # input_args = prepare_input_args(
        #      key, source, output_directory, prefix_map, node_property_predicates,
        #      predicate_mappings
        # )
        # output_args = prepare_output_args(
        #     key=None, # key,
        #     source="GOCams",
        #     output_directory=os.path.join(self.output_dir, self.source_name),
        #     reverse_prefix_map=None,
        #     reverse_predicate_mappings,
        #     property_types=np,
        # )
        # transformer = Transformer(stream=stream)
        # transformer.transform(input_args, output_args)
        # t = Transformer(stream=False)
        # t.transform(input_args=input_args, output_args=output_args)

        # this works and outputs nodes/edges, but it's not taking in cmap and np
        # transform(inputs=[data_file],
        #           input_format=input_format,
        #           input_compression=compression,
        #           output=os.path.join(self.output_dir, self.source_name),
        #           output_format='tsv')

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
