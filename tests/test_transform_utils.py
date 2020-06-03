import os
import tempfile
import unittest

from kg_covid_19.utils import write_node_edge_item


class TestTransformUtils(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.header = ['id', 'name', 'category']
        cls.valid_data = ['id1234', '1234', 'biolink:Gene']

    def setUp(self) -> None:
        self.tempdir = tempfile.gettempdir()
        self.outfile = os.path.join(self.tempdir, 'some.tsv')
        self.fh = open(self.outfile, 'w')

    def test_write_node_edge_item_bad_fh(self):
        with self.assertRaises(Exception):
            write_node_edge_item(fh='',  header=self.header, data=self.valid_data)

    def test_write_node_edge_item(self):
        write_node_edge_item(fh=self.fh,  header=self.header, data=self.valid_data)
        self.fh.close()
        self.assertTrue(os.path.exists(self.outfile))
        with open(self.outfile, 'r') as tsvfile:
            lines = tsvfile.read().split('\n')
            self.assertEqual(['id1234', '1234', 'biolink:Gene'], lines[0].split('\t'))

    def test_write_node_edge_item_with_tabs_in_data(self):
        write_node_edge_item(fh=self.fh,
                             header=self.header,
                             data=['id1234', '1234', 'biolink:Gene\tbiolink:Gene\t'],
                             sanitize_sep_char=True)
        self.fh.close()
        self.assertTrue(os.path.exists(self.outfile))
        with open(self.outfile, 'r') as tsvfile:
            lines = tsvfile.read().split('\n')
            self.assertEqual(['id1234',
                              '1234',
                              'biolink:Gene0x9biolink:Gene0x9'],
                              lines[0].split('\t'))


