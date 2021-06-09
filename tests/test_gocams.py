import io
import os
import sys
import tempfile
import unittest
from unittest import mock

from kg_covid_19.transform_utils.gocam_transform import GocamTransform


class TestGOCams(unittest.TestCase):

    def setUp(self) -> None:
        self.gc_nt_file = 'tests/resources/gocams/lifted-go-cams-20200619_SNIPPET.nt'
        self.input_dir = 'tests/resources/gocams/'
        self.output_dir = tempfile.mkdtemp()
        self.gocams_t = GocamTransform(input_dir=self.input_dir,
                                       output_dir=self.output_dir)

    def test_run(self):
        # Suppress chatter
        with mock.patch('sys.stdout', new=io.StringIO()) as std_out:
            self.gocams_t.run(data_file=self.gc_nt_file)
            sys.stdout = sys.__stdout__

    def test_run_exists(self):
        self.assertTrue(isinstance(self.gocams_t.run, object))
