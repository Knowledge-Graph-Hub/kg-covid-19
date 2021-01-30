from unittest import TestCase, mock

from kg_covid_19.transform_utils.scibite_cord import ScibiteCordTransform


class TestScibiteCord(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.input_dir = "tests/resources/scibite_cord"
        cls.output_dir = "tests/resources/scibite_cord"
        cls.scibite = ScibiteCordTransform(input_dir=cls.input_dir,
                                           output_dir=cls.output_dir)

    def test_run(self):
        self.scibite.run()
