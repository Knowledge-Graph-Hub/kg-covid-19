"""Test for query functions."""

import os
import pickle
import tempfile
from unittest import TestCase

import pandas as pd
from parameterized import parameterized

from kg_covid_19.query import parse_query_rq, result_dict_to_tsv


class TestQuery(TestCase):
    """Test query functions."""

    def setUp(self) -> None:
        """Set up for query function tests."""
        self.test_rq = "tests/resources/query/test_template.yaml"
        self.test_result_dict_file = "tests/resources/query/test_result_dict.pkl"
        self.tempfile = os.path.join(tempfile.mkdtemp(), "output.tsv")

    def test_parse_query_rq(self) -> None:
        """Test parsing a query in rq."""
        parse_query_rq(self.test_rq)

    def test_parse_query_rq_should_return_dict(self) -> None:
        """Test parsing a query in rq and returning a dict."""
        q = parse_query_rq(self.test_rq)
        self.assertTrue(isinstance(q, dict))

    @parameterized.expand(
        [
            ("title", "some title"),
            ("description", "what is it"),
            ("endpoint", "http://zombo.com"),
            (
                "query",
                """SELECT (COUNT(?v2) AS ?v1) ?v0
WHERE {
  ?v2 <https://w3id.org/biolink/vocab/category> ?v0
} GROUP BY ?v0
""",
            ),
        ]
    )
    def test_parse_query_rq_parameterized(self, key, value) -> None:
        """Test parsing a query with parameters."""
        q = parse_query_rq(self.test_rq)
        self.assertEqual(value, q[key])

    def test_result_dict_to_tsv_makes_file(self):
        """Test that result_dict converts to TSV."""
        result_dict = load_obj(self.test_result_dict_file)
        result_dict_to_tsv(result_dict, self.tempfile)
        self.assertTrue(os.path.isfile(self.tempfile))

    def test_result_dict_to_tsv_makes_correct_file(self):
        """Test that result_dict converts a TSV, as expected."""
        result_dict = load_obj(self.test_result_dict_file)
        result_dict_to_tsv(result_dict, self.tempfile)

        df = pd.read_csv(self.tempfile, sep="\t")
        self.assertEqual((18, 2), df.shape)
        self.assertEqual(["v1", "v0"], list(df.columns))
        self.assertEqual([10384, "human_phenotype"], list(df.iloc[1]))


def save_obj(obj, name):
    """Save an object as a pickle."""
    with open(name + ".pkl", "wb") as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    """Load an object from a pickle."""
    with open(name, "rb") as f:
        return pickle.load(f)
