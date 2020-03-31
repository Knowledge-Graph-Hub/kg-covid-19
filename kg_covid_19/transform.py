#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List

from kg_covid_19.transform_utils.drug_central.drug_central import DrugCentralTransform
from kg_covid_19.transform_utils.string_ppi import StringTransform
from kg_covid_19.transform_utils.zhou_host_proteins.zhou_transform import ZhouTransform


DATA_SOURCES = {
    'ZhouTransform': ZhouTransform,
    'DrugCentralTransform': DrugCentralTransform,
    'StringTransform': StringTransform
}

def transform(input_dir: str, output_dir: str, sources: List = None) -> None:
    """Call scripts in kg_covid_19/transform/[source name]/ to transform each source into a graph format that
    KGX can ingest directly, in either TSV or JSON format:
    https://github.com/NCATS-Tangerine/kgx/blob/master/data-preparation.md

    Args:
        input_dir: A string pointing to the directory to import data from.
        output_dir: A string pointing to the directory to output data to.
        sources: A list of sources to transform.

    Returns:
        None.
    """
    if not sources:
        # run all sources
        sources = DATA_SOURCES.keys()

    for source in sources:
        print(source)
        if source in DATA_SOURCES:
            if source == 'StringTransform':
                t = DATA_SOURCES[source](input_dir, output_dir)
            else:
                t = DATA_SOURCES[source]()
            t.run()
