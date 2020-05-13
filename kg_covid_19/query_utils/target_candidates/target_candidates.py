import builtins
import logging
import os
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
            os.path.join(self.input_dir, 'merged/kg-covid-19.tar.gz')
        self.merged_nodes_file = 'merged/merged-kg_nodes.tsv'
        self.merged_edges_file = 'merged/merged-kg_edges.tsv'
        self.sars_cov_2_nodes = "data/transformed/sars_cov_2_gene_annot/nodes.tsv"
        self.sars_cov_2_edges = "data/transformed/sars_cov_2_gene_annot/edges.tsv"

    def run(self):
        # extract TSV files
        tar = tarfile.open(self.merged_tsv_tarfile, "r:gz")
        tar.extractall()
        tar.close()

        # include SARS-CoV-2 proteins from gene annotation transform
        sars_cov2_df = pd.read_csv(self.sars_cov_2_nodes, sep="\t")
        self.sars_cov2_to_candidate_entry(sars_cov2_df)

        merged_nodes_df = pd.read_csv(os.path.join(self.input_dir, self.merged_nodes_file),
                               sep='\t')
        merged_edges_df = pd.read_csv(os.path.join(self.input_dir, self.merged_nodes_file),
                               sep='\t')
        # generate list of proteins that interact with SARS-CoV-2 according to IntAct
        pass

    def sars_cov2_to_candidate_entry(self,
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
