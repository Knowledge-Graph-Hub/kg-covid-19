#!/usr/bin/env python
# -*- coding: utf-8 -*-


from kg_covid_19.transform_utils import zhou_transform
from kg_covid_19.transform_utils.drug_central.drug_central import DrugCentralTransform
from kg_covid_19.transform_utils.string_ppi import StringTransform


def transform(input_dir: str, output_dir: str) -> None:
    """Call scripts in kg_covid_19/transform/[source name]/ to transform each source into a graph format that
    KGX can ingest directly, in either TSV or JSON format:
    https://github.com/NCATS-Tangerine/kgx/blob/master/data-preparation.md

    Args:
        input_dir: A string pointing to the directory to import data from.
        output_dir: A string pointing to the directory to output data to.

    Returns:
        None.
    """

    # call transform script for each source
    # TODO: refactor zhou_transform so that it accepts input.

    zhou_transform()

    dct = DrugCentralTransform()
    dct.run()

    string_ppi = StringTransform()
    string_ppi.run()
