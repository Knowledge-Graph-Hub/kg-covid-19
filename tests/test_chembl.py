"""Tests for the CHEMBL data parsing."""

import ast
from unittest import TestCase

from kg_covid_19.transform_utils.chembl import ChemblTransform


class TestChembl(TestCase):
    """Tests for the ChEMBL transform."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up the tests."""
        cls.chembl = ChemblTransform()
        cls.chembl_data_files = {
            "molecules_data": "tests/resources/chembl/chembl_molecule_records.json",
            "assay_data": "tests/resources/chembl/chembl_assay_records.json",
            "document_data": "tests/resources/chembl/chembl_document_records.json",
            "activity_data": "tests/resources/chembl/chembl_activity_records.json",
        }

        cls.chembl_activities_snippet_file = (
            "tests/resources/chembl/chembl_activities.snippet.txt"
        )
        cls.expected_ca_keys = [
            "standard_units",
            "standard_type",
            "standard_relation",
            "target_pref_name",
            "assay",
            "publications",
            "object",
            "subject",
            "assay_organism",
            "standard_value",
            "target_organism",
            "uo_units",
            "id",
            "predicate",
            "relation",
            "provided_by",
            "type",
        ]

    def setUp(self) -> None:
        """Set up the tests, but actually do that in setUpClass."""
        pass

    def test_run(self) -> None:
        """Test the CHEMBL transform."""
        self.assertTrue(hasattr(self.chembl, "run"))
        self.chembl.run(chembl_data_files=self.chembl_data_files)

    def test_source_name(self) -> None:
        """Test that the source name is ChEMBL."""
        self.assertEqual(self.chembl.source_name, "ChEMBL")

    def test_parse_chembl_activity(self):
        """Test that the input includes chembl activity."""
        self.chembl.input_base_dir = "."
        self.assertTrue(hasattr(self.chembl, "parse_chembl_activity"))

        with open(self.chembl_activities_snippet_file) as f:
            self.chembl_activities = []
            for line in f:
                self.chembl_activities.append(ast.literal_eval(line))
        ca = self.chembl.parse_chembl_activity(self.chembl_activities)
        self.assertEqual(len(ca), 5)
        self.assertEqual(self.expected_ca_keys, list(ca[0].keys()))
