from kg_covid_19.query_utils.query import Query


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

    def __init__(self, output_dir: str):
        pass

    def run(self):
        # generate list of SARS-CoV-2 proteins
        # generate list of proteins that interact with SARS-CoV-2 according to IntAct
        pass
