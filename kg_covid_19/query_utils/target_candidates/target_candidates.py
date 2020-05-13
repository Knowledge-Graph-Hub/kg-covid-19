import builtins
import logging
import os
import re
import tarfile
from typing import List, Union

from kg_covid_19.query_utils.query import Query
import pandas as pd  # type: ignore


class TargetCandidates(Query):
    """Perform a query of TSV files to generate a short list of protein targets
    for further investigation.

    A tsv file is emitted with these fields:
    species H=host, V=viral
    protein ID
    protein/gene name
    confidence score 0-1
    Free text describing why target was chosen

    This software is provided "as is" and any expressed or implied warranties,
    including, but not limited to, the implied warranties of merchantability and
    fitness for a particular purpose are disclaimed. in no event shall the authors or
    contributors be liable for any direct, indirect, incidental, special, exemplary, or
    consequential damages (including, but not limited to, procurement of substitute
    goods or services; loss of use, data, or profits; or business interruption)
    however caused and on any theory of liability, whether in contract, strict
    liability, or tort (including negligence or otherwise) arising in any way out of
    the use of this software, even if advised of the possibility of such damage.
    """

    def __init__(self, input_dir: str, output_dir: str):
        query_name = "target_candidates"
        super().__init__(query_name, input_dir, output_dir)  # set some variables
        # data file locations
        self.merged_tsv_tarfile =\
            os.path.join(self.input_dir, 'merged', 'kg-covid-19.tar.gz')
        self.merged_nodes_file = os.path.join('merged', 'merged-kg_nodes.tsv')
        self.merged_edges_file = os.path.join('merged', 'merged-kg_edges.tsv')
        self.sars_cov_2_nodes = os.path.join('data', "transformed",
                                             "sars_cov_2_gene_annot/nodes.tsv")
        self.sars_cov_2_edges = os.path.join('data', "transformed",
                                             "sars_cov_2_gene_annot/edges.tsv")

    def run(self) -> None:
        # extract TSV files
        tar = tarfile.open(self.merged_tsv_tarfile, "r:gz")
        tar.extractall(path=os.path.join("data", "merged"))
        tar.close()

        candidates: list = []

        # read in data files
        sars_cov2_df = pd.read_csv(self.sars_cov_2_nodes, sep="\t")
        merged_edges_df = pd.read_csv(os.path.join(self.input_dir,
                                                   self.merged_edges_file),
                                      sep='\t')
        merged_nodes_df = pd.read_csv(os.path.join(self.input_dir,
                                                   self.merged_nodes_file),
                                      sep='\t')

        # add SARS-CoV-2 proteins from gene annotation transform
        candidates.extend(
            self.sars_cov2_to_candidate_entries(sars_cov2_df,
                                              'V', 'id', 'name', 1,
                                              "annotated SARS-CoV-2 gene"))
        sars_cov2_ids = [c[1] for c in candidates]

        # append PRO_ SARS-CoV-2 proteins
        candidates.extend(
            self.sars_cov2_pro_candidates(sars_cov2_ids,
                                          sars_cov2_df,
                                          'V', 'id', 'name', 1,
                                          "annotated SARS-CoV-2 gene"))


        all_sars_cov2_ids = [c[1] for c in candidates]


        # append list of proteins that interact with SARS-CoV-2 according to IntAct
        candidates.extend(
        self.sars_cov2_and_intact_to_candidate_entries(all_sars_cov2_ids,
                                                       ['intact'],
                                                       merged_edges_df,
                                                       merged_nodes_df,
                                                       "H",
                                                       ['subject', 'object'],
                                                       ['name'],
                                                       0.75,
                                                       'inferred from intact')
        )

        self.candidates_to_tsv(candidates, self.output_dir, outfile_name)
        # import csv
        # data = ['text1', 'text2', 'text3', 'text4']
        # with open('output.tsv', 'w', newline='') as f_output:
        #     tsv_output = csv.writer(f_output, delimiter='\t')
        #     tsv_output.writerow(data)

    def sars_cov2_pro_candidates(self,
                                 these_ids: list,
                                 sars_cov2_df,
                                 viral_or_host: str,
                                 id_col: str,
                                 name_col: str,
                                 confidence_score: str,
                                 comments: str):
        """Given sars-cov-2 gene annotations, extract and make candidate entry
        :param IDs for which to look in nodes df for PRO_ genes
        :param sars_cov2_df:
        :param viral_or_host:
        :param id_col:
        :param name_col:
        :param confidence_score:
        :param comments:

        :return: List - candidate entry in format described in docstring
        """
        candidate_entries: list = []

        all_ids = list(sars_cov2_df[id_col])
        all_names = list(sars_cov2_df[name_col])
        for id_to_match in these_ids:
            this_re = re.compile(id_to_match)
            matching_indices = [i for i, item in enumerate(all_ids) if this_re.search(item)]

            for this_idx in matching_indices:
                this_id = all_ids[this_idx]
                this_name = all_names[this_idx]

                if this_id == id_to_match:  # don't match identical IDs
                    continue
                candidate_entry = [viral_or_host, this_id, this_name, confidence_score, comments]
                candidate_entries.append(candidate_entry)
        return candidate_entries


    def sars_cov2_to_candidate_entries(self,
                                       sars_cov2_df,
                                       viral_or_host: str,
                                       id_col: str,
                                       name_col: str,
                                       confidence_score: str,
                                       comments: str
                                       ) -> List[List[Union[str, int]]]:
        """Given sars-cov-2 gene annotations, extract and make candidate entry

        :param comments:
        :param confidence_score:
        :param name_col:
        :param id_col:
        :param viral_or_host:
        :param sars_cov2_df:
        :return: List - candidate entry in format described in docstring
        """
        candidate_entries: list = []

        for _, row in sars_cov2_df.iterrows():
            candidate_entry = [viral_or_host, None, None, confidence_score, comments]
            if id_col in row:
                candidate_entry[1] = row[id_col]
            if name_col in row:
                candidate_entry[2] = row[name_col]
            candidate_entries.append(candidate_entry)
        return candidate_entries


    def sars_cov2_and_intact_to_candidate_entries(self,
                                                  sars_cov2_ids: list,
                                                  provided_by: list,
                                                  edge_df,
                                                  nodes_df,
                                                  viral_or_host: str,
                                                  id_cols: list,
                                                  name_col: str,
                                                  confidence_score: str,
                                                  comments: str
                                                  ) -> List[List[Union[str, int]]]:
        """Given sars-cov-2 genes and a pandas DF with edge data and node data, extract
        all proteins that interact with these sars-cov2 genes according to source(s) in
        'provided_by'

        :param sars_cov2_ids
        :param provided_by
        :param edge_df
        :param node_df
        :param viral_or_host:
        :param id_col:
        :param edge_df,
        :param comments:
        :param confidence_score:
        :param name_col:
        :param sars_cov2_df:
        :return: List - candidate entry in format described in docstring
        """
        candidate_entries: list = []

        # for _, row in sars_cov2_df.iterrows():
        #     candidate_entry = [viral_or_host, None, None, confidence_score, comments]
        #     if id_col in row:
        #         candidate_entry[1] = row[id_col]
        #     if name_col in row:
        #         candidate_entry[2] = row[name_col]
        #     candidate_entries.append(candidate_entry)
        return candidate_entries
