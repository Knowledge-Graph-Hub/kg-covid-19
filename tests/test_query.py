from unittest import TestCase

from parameterized import parameterized

from kg_covid_19.query import parse_query_yaml


class TestQuery(TestCase):
    """Tests query functions()
    """

    def setUp(self) -> None:
        self.test_yaml = 'tests/resources/query/test_template.yaml'

    def test_parse_query_yaml(self) -> None:
        parse_query_yaml(self.test_yaml)

    def test_parse_query_yaml_should_be_dict(self) -> None:
        q = parse_query_yaml(self.test_yaml)
        self.assertTrue(isinstance(q, dict))

    @parameterized.expand([
        ('title', 'some title'),
        ('description', 'what is it'),
        ('endpoint', 'http://zombo.com'),
        ('query', """SELECT (COUNT(?v2) AS ?v1) ?v0 WHERE {
  ?v2 <https://w3id.org/biolink/vocab/category> ?v0
} GROUP BY ?v0
""")
    ])
    def test_parse_query_yaml_should_be_dict(self, key, value) -> None:
        q = parse_query_yaml(self.test_yaml)
        self.assertEqual(value, q[key])
