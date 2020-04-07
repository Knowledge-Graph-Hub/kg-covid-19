#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from typing import List

from kg_covid_19.transform_utils.drug_central.drug_central import DrugCentralTransform
from kg_covid_19.transform_utils.hpo.hpo import HpoTransform
from kg_covid_19.transform_utils.\
    sars_cov_2_gene_annot.sars_cov_2_gene_annot import SARSCoV2GeneAnnot
from kg_covid_19.transform_utils.scibite_cord import ScibiteCordTransform
from kg_covid_19.transform_utils.pharmgkb import PharmGKB
from kg_covid_19.transform_utils.string_ppi import StringTransform
from kg_covid_19.transform_utils.ttd.ttd import TTDTransform
from kg_covid_19.transform_utils.zhou_host_proteins.zhou_transform import ZhouTransform


DATA_SOURCES = {
    'ZhouTransform': ZhouTransform,
    'DrugCentralTransform': DrugCentralTransform,
    'HpoTransform': HpoTransform,
    'TTDTransform': TTDTransform,
    'StringTransform': StringTransform,
    'ScibiteCordTransform': ScibiteCordTransform,
    'PharmGKB': PharmGKB,
    'SARSCoV2GeneAnnot': SARSCoV2GeneAnnot
}


def transform(input_dir: str, output_dir: str, sources: List[str] = None) -> None:
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
        sources = list(DATA_SOURCES.keys())

    for source in sources:
        if source in DATA_SOURCES:
            logging.info(f"Parsing {source}")
            t = DATA_SOURCES[source](input_dir, output_dir)
            t.run()
