from kg_emerging_viruses.transform_utils import zhou_transform
from kg_emerging_viruses.transform_utils.drug_central.drug_central import \
    DrugCentralTransform


def transform(input_dir, output_dir):
    """
    Call scripts in kg_emerging_viruses/transform/[source name]/
    to transform each source into a graph format that KGX can
    ingest directly, in either TSV or JSON format:
    https://github.com/NCATS-Tangerine/kgx/blob/master/data-preparation.md
    """

    # call transform script for each source
    # TODO: refactor zhou_transform so that it accepts input.
    zhou_transform()

    dct = DrugCentralTransform()
    dct.run()
