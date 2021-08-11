Quick Start
-----------

.. code:: sh

       git clone https://github.com/Knowledge-Graph-Hub/kg-covid-19
       cd kg-covid-19
       python3 -m venv venv && source venv/bin/activate # optional
       pip install .
       python run.py download
       python run.py transform
       python run.py merge

Download the Knowledge Graph
----------------------------

Prebuilt versions of the KG-COVID-19 knowledge graph build from all
available data are available in the following serialization formats:

* `RDF N-Triples <http://kg-hub.berkeleybop.io/kg-covid-19/current/kg-covid-19.nt.gz>`__
* `KGX TSV <http://kg-hub.berkeleybop.io/kg-covid-19/current/kg-covid-19.tar.gz>`__

See `here <https://github.com/biolink/kgx/blob/master/specification/kgx-format.md>`__
for a description of the KGX TSV format

Previous builds are available for download
`here <https://kg-hub.berkeleybop.io/kg-covid-19/>`__. Each build
contains the following data:

* ``raw``: the data ingested for this build
* ``transformed``: the transformed data from each source
* ``stats``: detailed statistics about the contents of the KG
* ``Jenkinsfile``: the exact commands used to generate the KG
* ``kg-covid-19.nt.gz``: an RDF/Ntriples version of the KG
* ``kg-covid-19.tar.gz``: a KGX TSV version of the KG
* ``kg-covid-19.jnl.gz``: the Blazegraph journal file (for loading an endpoint)

Knowledge Graph Hub concept
---------------------------

A Knowledge Graph Hub (KG Hub) is framework to download and transform
data to a central location for building knowledge graphs (KGs) from
different combination of data sources, in an automated, YAML-driven way.
The workflow constitutes of 3 steps:

* Download data
* Transform data for each data source into two TSV files (``edges.tsv`` and ``nodes.tsv``) as specified `here <https://github.com/NCATS-Tangerine/kgx/blob/master/data-preparation.md>`__
* Merge the graphs for each data source of interest using `KGX <https://github.com/NCATS-Tangerine/kgx/>`__ to produce a merged knowledge graph

To facilitate interoperability of datasets, `Biolink
categories <https://biolink.github.io/biolink-model/docs/category.html>`__
are added to nodes and `Biolink association
types <https://biolink.github.io/biolink-model/docs/Association>`__ are
added to edges during transformation.

A more thorough explanation of the KG-hub concept is
`here <https://knowledge-graph-hub.github.io/>`__.

KG-COVID-19 project
-------------------

The `KG-COVID-19 <https://github.com/Knowledge-Graph-Hub/kg-covid-19/>`__
project is the first instantiation of such a KG Hub. Thus, KG-COVID-19
is a framework that follows design patterns of the KG Hub to download
and transform COVID-19/SARS-COV-2 related datasets and emit a knowledge
graph that can then be used for machine learning or others uses, to
produce actionable knowledge.

The codebase
~~~~~~~~~~~~

-  `Here <https://github.com/Knowledge-Graph-Hub/kg-covid-19>`__ is the
   GitHub repo for this project.
-  `Here <https://github.com/monarch-initiative/embiggen>`__ is the
   GitHub repo for Embiggen, an implementation of node2vec and other
   methods to generate embeddings and apply machine learning to graphs.
-  `Here <https://github.com/NCATS-Tangerine/kgx/>`__ is the GitHub repo
   for KGX, a knowledge graph exchange tool for working with graphs

Prerequisites
~~~~~~~~~~~~~

-  Java/JDK is required in order for the transform step to work
   properly. See
   `here <https://docs.oracle.com/en/java/javase/15/install/overview-jdk-installation.html#GUID-8677A77F-231A-40F7-98B9-1FD0B48C346A>`__
   for instructions on installing.

Computational requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~

-  On a commodity server with 200 GB of memory, generation of the
   knowledge graph containing all source data requires a total of 3.7
   hours (0.13 hours, 1.5 hours, and 2.1 hours for the download,
   transform, and merge step, respectively), with a peak memory usage of
   34.4 GB and disk use of 37 GB. An estimate of the current build time
   on a typical server is also available
   `here <https://build.berkeleybop.io/job/knowledge-graph-hub/job/kg-covid-19/job/master/>`__.

Installation
~~~~~~~~~~~~

.. code:: sh

       git clone https://github.com/Knowledge-Graph-Hub/kg-covid-19
       cd kg-covid-19
       python3 -m venv venv && source venv/bin/activate # optional
       pip install .

Running the pipeline
~~~~~~~~~~~~~~~~~~~~

.. code:: sh

       python run.py download
       python run.py transform
       python run.py merge

Jupyter notebook
~~~~~~~~~~~~~~~~

We have also prepared a `Jupyter
notebook <https://github.com/Knowledge-Graph-Hub/kg-covid-19/blob/master/example-KG-COVID-19-usage.ipynb>`__
demonstrating how to run the pipeline to generate a KG, and also how to
use other tooling such as graph sampling for generating holdouts, and
graph querying.

A few organizing principles used for data ingest
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  UniProtKB identifiers are used for genes and proteins, where possible
-  For drug/compound identifiers, there is a preferred namespace. If
   there are datasets that provide identifiers from multiple namespaces
   then the choice is determined based on a descending order of
   preference,

   -  ``CHEBI`` > ``CHEMBL`` > ``DRUGBANK`` > ``PUBCHEM``

-  Less is more: for each data source, we ingest only the subset of data
   that is most relevant to the knowledge graph in question (here, it’s
   KG-COVID-19)
-  We avoid ingesting data from a source that isn’t authoritative for
   the data in question (e.g. we do not ingest protein interaction data
   from a drug database)
-  Each ingest should make an effort to add provenance data by adding a
   ``provided_by`` column for each node and edge in the output TSV file,
   populated with the source of each datum

Querying the graph
------------------

A SPARQL endpoint for the merged knowledge graph is available
`here <http://kg-hub-rdf.berkeleybop.io/blazegraph/#query>`__. For a
better experience, consider using https://yasgui.triply.cc/ for your
querying needs (for yasgui, set
http://kg-hub-rdf.berkeleybop.io/blazegraph/sparql as your SPARQL
endpoint). If you are not sure where to start, here are some example
SPARQL queries:
https://github.com/Knowledge-Graph-Hub/kg-covid-19/tree/master/queries/sparql

Summary of the data
~~~~~~~~~~~~~~~~~~~

A detailed, up-to-date summary of data in KG-COVID-19 is available
`here <https://kg-hub.berkeleybop.io/kg-covid-19/current/stats/merged_graph_stats.yaml>`__,
with contents of the knowledge graph broken down by Biolink categories
and Biolink association types for nodes and edges, respectively.

An interactive dashboard to explore these stats is available
`here <https://knowledge-graph-hub.github.io/kg-covid-19-dashboard/>`__.

How to Contribute
-----------------

Download and use the code
~~~~~~~~~~~~~~~~~~~~~~~~
Download and use the code, and any issues and questions
`here <https://github.com/Knowledge-Graph-Hub/kg-covid-19/issues/new/choose>`__.

Write code to ingest data
~~~~~~~~~~~~~~~~~~~~~~~~

Most urgent need is for code to ingest data from new sources.

**Find a data source to ingest:**

An issue tracker with a list of new data sources is
`here <https://github.com/Knowledge-Graph-Hub/kg-covid-19/labels/new%20data%20source>`__.

**Look at the data file(s), and plan how you are going to write out data
to nodes and edges:**

You’ll need to write out a ``nodes.tsv`` file describing each entity you
are ingesting, and an ``edges.tsv`` describing the relationships between
entities, as described
`here <https://github.com/NCATS-Tangerine/kgx/blob/master/data-preparation.md>`__.

``nodes.tsv`` should have at least these columns (you can add more
columns if you like):

``id  name    category``

``id`` should be a CURIE that uses one of `these
identifiers <https://biolink.github.io/biolink-model/#identifiers>`__.
They are enumerated
`here <https://biolink.github.io/biolink-model/context.jsonld>`__. For
genes, a Uniprot ID is preferred, if available.

``category`` should be a `Biolink
category <https://biolink.github.io/biolink-model/docs/category.html>`__
in CURIE format, for example ``biolink:Gene``

``edges.tsv`` should have at least these columns:

``subject edge_label  object   relation``

``subject`` and ``object`` should be ``id``\ s that are present in the
``nodes.tsv`` file (again, as CURIEs that uses one of
`these <https://biolink.github.io/biolink-model/#identifiers>`__).
``edge_label`` should be a CURIE for the `biolink
edge_label <https://biolink.github.io/biolink-model/docs/edge_label>`__
that describes the relationship. ``relation`` should be a CURIE for the
term from the `relation
ontology <https://www.ebi.ac.uk/ols/ontologies/ro>`__.

**Read how to make a PR, and fork the repo:**

-  Read
   `these <https://github.com/Knowledge-Graph-Hub/kg-covid-19/blob/master/CONTRIBUTING.md>`__
   instructions about how to make a pull request in github. Fork the
   code and set up your development environment.

**Add a block to ``download.yaml`` to download data file for source:**

-  Add a block of yaml containing the url of the file you need to
   download for the source (and optionally a brief description) in
   `download.yaml <https://github.com/Knowledge-Graph-Hub/kg-covid-19/blob/master/download.yaml>`__
   like so - each item will be downloaded when the ``run.py download``
   command is executed:

.. code-block:: yaml

    #
    # brief comment about this source, one or more blocks with a url: (and optionally a local_name:, to avoid name collisions)
    #
    -
      # first file
      url: http://curefordisease.org/some_data.txt
      local_name: some_data.txt
    -
      # second file
      url: http://curefordisease.org/some_more_data.txt
      local_name: some_more_data.txt


**Add code to ingest and transform data:**

*  Add a new sub-directory in `kg_emerging_viruses/transform_utils <https://github.com/Knowledge-Graph-Hub/kg-covid-19/tree/master/kg_emerging_viruses/transform_utils>`__
   with a unique name for your source. If the data come from a
   scientific paper, consider prepending the pubmed ID to the name of
   the source (e.g. ``pmid28355270_hcov229e_a549_cells``)

*  In this sub-directory, write a class that ingests the file(s) you
   added above in the yaml, which will be in
   ``data/raw/[file name without path]``. Your class should have a
   constructor and a ``run()`` function, which is called to perform the
   ingest. It should output data into ``data/transformed/[source name]``
   for all nodes and edges, in tsv format, as described `here <https://github.com/NCATS-Tangerine/kgx/blob/master/data-preparation.md>`__.

*  Also add the following metadata in the comments of your script:
    * data source
    * files used
    * release version that you are ingesting
    * documentation on which fields are relevant and how they map to node and edge properties
    * In `kg_covid_19/transform.py <https://github.com/Knowledge-Graph-Hub/kg-covid-19/blob/master/kg_covid_19/transform.py>`__, add a key/value pair to ``DATA_SOURCES``. The key should be the ``[source name]`` above, and the value should be the name of the class above. Also add an import statement for the class.
    * In `merge.yaml <https://github.com/Knowledge-Graph-Hub/kg-covid-19/blob/master/merge.yaml>`__, add a block for your new source, something like:

.. code-block:: yaml

    SOURCE_NAME:
      input:
        format: tsv
        filename:
        - data/transformed/[source_name]/nodes.tsv
        - data/transformed/[source_name]/edges.tsv\

**Submit your PR on github, and link the github issue for the data
source you ingested**

Might want to run ``pylint`` and ``mypy`` and fix any issues before
submitting your PR.

Develop jupyter notebooks to show how to use kg-covid-19
~~~~~~~~~~~~~~~~~~~~~~~~

See `here <https://github.com/Knowledge-Graph-Hub/kg-covid-19/blob/master/example-KG-COVID-19-usage.ipynb>` for example. Please contact `Justin <justaddcoffee@gmail.com>`__ or
anyone on the development team if you’d like to help!

Contributors
------------

-  `Justin Reese <https://github.com/justaddcoffee>`__
-  `Deepak Unni <https://github.com/deepakunni3>`__
-  `Marcin Joachimiak <https://github.com/realmarcin>`__
-  `Peter Robinson <https://github.com/pnrobinson>`__
-  `Chris Mungall <https://github.com/cmungall>`__
-  `Tiffany Callahan <https://github.com/callahantiff>`__
-  `Luca Cappelletti <https://github.com/LucaCappelletti94>`__
-  `Vida Ravanmehr <https://github.com/vidarmehr>`__

Acknowledgements
----------------

We gratefully acknowledge and thank all COVID-19 data providers for
making their data available.
