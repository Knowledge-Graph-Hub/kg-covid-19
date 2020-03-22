# KG Hub

This repository aims to be a first pass at building a KG Hub.

The motivation of a KG Hub is to have a central location to store configurations for building knowledge graphs (KGs) 
from different combinations of data sources, all driven by a YAML.


## KG Hub instance

Each KG Hub instance is represented by a YAML.

The YAML defines the following,
- Data sources (or subsets) to be ingested
- Metadata about the KG


### Format of YAML

> TBD

## KGX and KG Hub YAML

The overall goal is to have [KGX](https://github.com/NCATS-Tangerine/kgx/) read from this YAML, 
load all data sources (as defined in the YAML) and build a KG.

Ideally, each data source should be preprocessed ahead of time to a format as prescribed [here](https://github.com/NCATS-Tangerine/kgx/blob/master/data-preparation.md).

 