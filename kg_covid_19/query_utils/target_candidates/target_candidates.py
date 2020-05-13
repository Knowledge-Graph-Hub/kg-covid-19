import os
import tarfile
from kg_covid_19.query_utils.query import Query
import pandas as pd  # type: ignore


class TargetCandidates(Query):
    """Perform a query of TSV files to generate a short list of protein targets
    for further investigation.

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
        self.nodes_file = 'merged-kg_nodes.tsv'
        self.edges_file = 'merged-kg_edges.tsv'

    def run(self):
        # extract TSV files
        tsv_tarfile = os.path.join(self.input_dir, 'kg-covid-19.tar.gz')
        tar = tarfile.open(tsv_tarfile, "r:gz")
        tar.extractall()
        tar.close()

        # generate list of SARS-CoV-2 proteins
        nodes_df = pd.read_csv(os.path.join(self.input_dir, self.nodes_file),
                                         sep='\t')
        edges_df = pd.read_csv(os.path.join(self.input_dir, self.edges_file),
                                         sep='\t')
        # generate list of proteins that interact with SARS-CoV-2 according to IntAct
        pass
