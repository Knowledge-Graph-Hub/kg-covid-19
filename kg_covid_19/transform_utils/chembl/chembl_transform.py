import json
import os
import elasticsearch
import elasticsearch.helpers

import compress_json  # type: ignore
from typing import Optional, Set, Dict, List
from tqdm import tqdm # type: ignore

from kg_covid_19.transform_utils.transform import Transform
from kg_covid_19.utils import write_node_edge_item


TAXON_MAP = {
    'Severe acute respiratory syndrome coronavirus 2': 'NCBITaxon:2697049',
    'SARS-CoV-2': 'NCBITaxon:2697049',
}


class ChemblTransform(Transform):
    """
    Parse ChEMBL and transform them into a property graph representation.
    """

    def __init__(self, input_dir: str = None, output_dir: str = None,
                 host: str = 'https://www.ebi.ac.uk/chembl/elk/es/'):
        source_name = 'ChEMBL'
        super().__init__(source_name, input_dir, output_dir)
        self.subset = 'SARS-CoV-2 subset'
        self._end = None
        self._node_header: Set = set()
        self._edge_header: Set = set()
        self.es_conn = elasticsearch.Elasticsearch(hosts=[host])

    def run(self, data_file: Optional[str] = None) -> None:
        """Method is called and performs needed transformations to process
        SARS-CoV-2 subset of ChEMBL.

        http://chembl.blogspot.com/2020/05/chembl27-sars-cov-2-release.html

        Args:
            data_file: data file to parse

        Returns:
            None.

        """
        self.node_header = ['id', 'name', 'category', 'provided_by']
        self.edge_header = ['id', 'subject', 'predicate', 'object', 'relation', 'provided_by', 'type']

        # ChEMBL molecules
        data = self.get_chembl_molecules()
        molecule_nodes = self.parse_chembl_molecules(data)

        # ChEMBL assay
        data = self.get_chembl_assays()
        assay_nodes = self.parse_chembl_assay(data)

        # ChEMBL document
        data = self.get_chembl_documents()
        document_nodes = self.parse_chembl_document(data)

        # ChEMBL activity
        data = self.get_chembl_activities()
        activity_edges = self.parse_chembl_activity(data)

        self.node_header.extend([x for x in self._node_header if x not in self.node_header])
        self.edge_header.extend([x for x in self._edge_header if x not in self.edge_header])

        node_handle = open(self.output_node_file, 'w')
        edge_handle = open(self.output_edge_file, 'w')
        node_handle.write("\t".join(sorted(self.node_header)) + "\n")
        edge_handle.write("\t".join(sorted(self.edge_header)) + "\n")

        for n in molecule_nodes:
            write_node_edge_item(
                fh=node_handle,
                header=sorted(self.node_header),
                data=[n[x] if x in n else '' for x in sorted(self.node_header)]
            )
        for n in assay_nodes:
            write_node_edge_item(
                fh=node_handle,
                header=sorted(self.node_header),
                data=[n[x] if x in n else '' for x in sorted(self.node_header)]
            )

        for n in document_nodes:
            write_node_edge_item(
                fh=node_handle,
                header=sorted(self.node_header),
                data=[n[x] if x in n else '' for x in sorted(self.node_header)]
            )

        # write node for organisms in TAXON_MAP
        for org_curie, org_name in {v: k for k, v in TAXON_MAP.items()}.items():
            o = {'id': org_curie, 'name': org_name, 'category': 'biolink:OrganismTaxon'}
            write_node_edge_item(
                fh=node_handle,
                header=sorted(self.node_header),
                data=[o[x] if x in o else '' for x in sorted(self.node_header)]
            )

        for e in activity_edges:
            write_node_edge_item(
                fh=edge_handle,
                header=sorted(self.edge_header),
                data=[e[x] if x in e else '' for x in sorted(self.edge_header)]
            )

    def parse_chembl_activity(self, data: List):
        """Parse ChEMBL Activity records.

        An activity document links 4 entities,
            - assay
            - document
            - target
            - molecule

        Each of the activity document will be converted to an edge that links
        a molecule to a target with biolink:interacts_with edge_label.
        The edge itself will have additional properties like 'publications' and 'assay'
        that references the publication and assay, respectively.
        The edge will also have measurements as edge properties that describe the
        activity/interaction further.

        Args:
            data: A list of ChEMBL Activity records

        Returns:
            A list

        """
        edge_label = 'biolink:interacts_with'
        relation = 'RO:0002436'
        allowed_properties = {
            'assay_organism', 'assay_chembl_id', 'document_chembl_id', 'target_chembl_id', 'target_organism', 'target_pref_name',
            'molecule_chembl_id', 'standard_units', 'standard_type', 'standard_relation', 'standard_value', 'uo_units'
        }
        remap = {
            'molecule_chembl_id': 'subject',
            'target_chembl_id': 'object',
            'document_chembl_id': 'publications',
            'assay_chembl_id': 'assay'
        }
        self._edge_header.update([remap[x] if x in remap else x for x in allowed_properties])

        edges = []
        for record in data:
            activity_id = record['_source']['activity_id']
            edge_properties = self.parse_doc_fields(record['_source'], allowed_properties, remap)
            edge_properties['id'] = str(activity_id)
            edge_properties['predicate'] = edge_label
            edge_properties['relation'] = relation
            edge_properties['subject'] = f"CHEMBL.COMPOUND:{edge_properties['subject']}"
            edge_properties['object'] = f"CHEMBL.TARGET:{edge_properties['object']}"
            if 'target_organism' in edge_properties:
                # remap CHEMBL.TARGET that are just references to SARS-CoV-2
                if edge_properties['target_organism'] in TAXON_MAP:
                    edge_properties['object'] = TAXON_MAP[edge_properties['target_organism']]
            edge_properties['assay'] = f"CHEMBL.ASSAY:{edge_properties['assay']}"
            if edge_properties['uo_units']:
                edge_properties['uo_units'] = edge_properties['uo_units'].replace('_', ':')
            edge_properties['provided_by'] = f"{self.source_name} {self.subset}"
            edge_properties['type'] = 'biolink:Association'
            edges.append(edge_properties)
        return edges

    def parse_chembl_molecules(self, data: List):
        """Parse ChEMBL Molecule records.

        Args:
            data: A list of ChEMBL Molecule records

        Returns:
            A list
        """
        node_category = ['biolink:Drug']
        allowed_properties = {
            'molecule_type', 'polymer_flag', 'inorganic_flag', 'natural_product',
            'synonyms', 'molecule_properties', 'canonical_smiles', 'full_molformula',
            'pref_name'
        }
        remap = {
            'pref_name': 'name',
            'full_molformula': 'molecular_formula',
            'synonyms': 'synonym'
        }
        self._node_header.update([remap[x] if x in remap else x for x in allowed_properties])

        nodes = []
        for record in data:
            molecule_id = record['_source']['molecule_chembl_id']
            node_properties = self.parse_doc_fields(record['_source'], allowed_properties, remap)
            node_properties['category'] = '|'.join(node_category)
            node_properties['id'] = f"CHEMBL.COMPOUND:{molecule_id}"
            node_properties['provided_by'] = f"{self.source_name} {self.subset}"
            nodes.append(node_properties)
        return nodes

    def parse_chembl_assay(self, data: List):
        """Parse ChEMBL Assay records.

        Args:
            data: A list of ChEMBL Assay records

        Returns:
            A list
        """
        node_category = ['biolink:Assay']
        node_type = 'SIO:001007'
        allowed_properties = {
            'assay_type', 'assay_tax_id', 'assay_cell_type', 'assay_tissue',
            'assay_strain', 'description', 'assay_chembl_id', 'document_chembl_id',
            'tissue_chembl_id', 'confidence_score', 'bao_format', 'bao_label'
        }
        remap = {
            'assay_cell_type': 'cell_type',
            'assay_tissue': 'tissue',
            'assay_strain': 'strain',
            'assay_tax_id': 'in_taxon',
            'document_chembl_id': 'publications'
        }
        self._node_header.update([remap[x] if x in remap else x for x in allowed_properties])

        nodes = []
        for record in data:
            assay_id = record['_source']['assay_chembl_id']
            node_properties = self.parse_doc_fields(record['_source'], allowed_properties)
            node_properties['id'] = f"CHEMBL.ASSAY:{assay_id}"
            node_properties['category'] = '|'.join(node_category)
            node_properties['node_type'] = node_type
            if node_properties['bao_format']:
                node_properties['bao_format'] = node_properties['bao_format'].replace('_', ':')
            node_properties['provided_by'] = f"{self.source_name} {self.subset}"
            nodes.append(node_properties)
        return nodes

    def parse_chembl_document(self, data: List):
        """Parse ChEMBL Document records.

        Args:
            data: A list of ChEMBL Document records

        Returns:
            A list
        """
        node_category = ['biolink:Publication']
        allowed_properties = {
            'title', 'pubmed_id', 'doi'
        }
        remap: Dict = {}
        self._node_header.update([remap[x] if x in remap else x for x in allowed_properties])

        nodes = []
        for record in data:
            document_id = record['_source']['document_chembl_id']
            node_properties = self.parse_doc_fields(record['_source'], allowed_properties)
            if node_properties['pubmed_id']:
                node_properties['id'] = f"PMID:{node_properties['pubmed_id']}"
            elif node_properties['doi']:
                node_properties['id'] = f"DOI:{node_properties['doi']}"
            else:
                node_properties['id'] = f"CHEMBL.DOCUMENT:{document_id}"
            node_properties['category'] = '|'.join(node_category)
            node_properties['provided_by'] = f"{self.source_name} {self.subset}"
            nodes.append(node_properties)
        return nodes

    def parse_doc_fields(self, record: dict, allowed_properties: set, remap: dict = None):
        """Parse a record from the API.

        Args:
            record: The record or document from the API
            allowed_properties: properties that are to be parsed
            remap: properties that are to be remapped from one name to another

        Returns:
            A dict of properties

        """
        properties: Dict = {}

        def update_properties(key, value):
            """update properties dictionary in a
            sensible manner.
            """
            if key in properties:
                if isinstance(properties[key], str):
                    properties[key] = [properties[key]]
                properties[key].append(value)
            else:
                properties[key] = value

        for k, v in record.items():
            if isinstance(v, dict):
                if k in allowed_properties:
                    for k2, v2 in v.items():
                        if remap and k2 in remap.keys():
                            update_properties(remap[k2], v2)
                        else:
                            update_properties(k2, v2)
                else:
                    r = self.parse_doc_fields(v, allowed_properties, remap)
                    for k2, v2 in r.items():
                        update_properties(k2, v2)
            elif isinstance(v, list):
                if k in allowed_properties:
                    if remap and k in remap.keys():
                        update_properties(remap[k], str(v) if v else '')
                    else:
                        update_properties(k, str(v) if v else '')
                else:
                    if len(v) and isinstance(v[0], dict):
                        for x in v:
                            r = self.parse_doc_fields(x, allowed_properties, remap)
                            for k2, v2 in r.items():
                                update_properties(k2, v2)
            else:
                if k in allowed_properties:
                    if remap and k in remap.keys():
                        update_properties(remap[k], str(v) if v else '')
                    else:
                        update_properties(k, str(v) if v else '')

        for k, v in properties.items():
            if isinstance(v, list):
                properties[k] = '|'.join(v)

        return properties

    def get_chembl_activities(self):
        """Get ChEMBL activities by querying the ChEMBL Activity Resource.

        Args:

        Returns:
            A list of ChEMBL activity records
        """
        index = 'chembl_28_activity'
        query_data = compress_json.local_load('chembl_activity_query.json')
        output = open(os.path.join(self.input_base_dir, 'chembl_activity_records.json'), 'w')
        activities = self.get_records(index, query_data)
        json.dump(activities, output)
        return activities

    def get_chembl_molecules(self):
        """Get ChEMBL molecules by querying the ChEMBL Molecule Resource.

        Args:
            start: query start

        Returns:
            A list of ChEMBL molecule records
        """
        index = 'chembl_28_molecule'
        query_data = compress_json.local_load('chembl_molecule_query.json')
        output = open(os.path.join(self.input_base_dir, 'chembl_molecule_records.json'), 'w')
        molecules = self.get_records(index, query_data)
        json.dump(molecules, output)
        return molecules

    def get_chembl_documents(self):
        """Get ChEMBL documents by querying the ChEMBL Document Resource.

        Args:

        Returns:
            A list of ChEMBL document records
        """
        index = 'chembl_28_document'
        query_data = compress_json.local_load('chembl_document_query.json')
        output = open(os.path.join(self.input_base_dir, 'chembl_document_records.json'), 'w')
        documents = self.get_records(index, query_data)
        json.dump(documents, output)
        return documents

    def get_chembl_assays(self):
        """Get ChEMBL assays by querying the ChEMBL Assay Resource.

        Args:

        Returns:
            A list of ChEMBL assay records
        """
        index = 'chembl_28_assay'
        query_data = compress_json.local_load('chembl_assay_query.json')
        output = open(os.path.join(self.input_base_dir, 'chembl_assay_records.json'), 'w')
        assays = self.get_records(index, query_data)
        json.dump(assays, output)
        return assays

    def get_records(self,
                    index,
                    query,
                    scroll: str = u'1m',
                    request_timeout: int = 60,
                    preserve_order: bool = True,
                    ):
        """Fetch records from the given URL and query parameters.

        Args:
            index: the elastic search index for query
            query: query
            scroll: scroll parameter passed to elastic search
            request_timeout: timeout parameter passed to elastic search
            preserve_order: preserve order param passed to elastic search
        Returns:
            All records for query
        """
        records = []
        results = elasticsearch.helpers.scan(self.es_conn,
                                             index=index,
                                             scroll=scroll,
                                             request_timeout=request_timeout,
                                             preserve_order=preserve_order,
                                             query=query)

        for item in tqdm(results, desc="querying for index: " + index):
            records.append(item)

        return records


