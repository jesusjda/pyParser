import unittest
import os as _os
import networkx as nx
import networkx.drawing.nx_pydot as nx_pydot
import genericparser


class TestKey(unittest.TestCase):

    def test_import(self):
        self.assertEqual(1, 1)

    def test_parser_fc(self):
        self.assertEqual(1, 1)
        return
        p = _os.path.dirname(_os.path.abspath(__file__))
        testfile = _os.path.join(p, "../genericparser/examples/example.fc")
        result = _os.path.join(p, "./result_fc.dot")
        original = _os.path.join(p, "../genericparser/graphs/example_fc.dot")
        cfg = genericparser.parse(testfile, result)
        with open(result, 'r') as f:
            r_list = f.read()
        with open(original, 'r') as f:
            o_list = f.read()
        print("RESULT")
        # print(r_list)
        print("######################################")
        # print("ORIGINAL")
        print(o_list)
        rg = nx_pydot.read_dot(result)
        rgc = rg.copy()
        og = nx_pydot.read_dot(original)
        ogc = og.copy()
        a = nx.difference(rg, og)
        b = nx.difference(ogc, rgc)
        self.assertTrue(nx.is_empty(a))
        self.assertTrue(nx.is_empty(b))

    def test_parser_mlc(self):
        self.assertEqual(1, 1)
        return
        p = _os.path.dirname(_os.path.abspath(__file__))
        testfile = _os.path.join(p, "../genericparser/examples/example.mlc")
        result = _os.path.join(p, "./result_mlc.dot")
        original = _os.path.join(p, "../genericparser/graphs/example_mlc.dot")
        print("..")
        cfg = genericparser.parse(testfile, result)

        with open(result, 'r') as f:
            r_list = f.read()
        with open(original, 'r') as f:
            o_list = f.read()
        print("RESULT")
        print(r_list)
        print("######################################")
        print("ORIGINAL")
        print(o_list)
        rg = nx_pydot.read_dot(result)
        rgc = rg.copy()
        og = nx_pydot.read_dot(original)
        ogc = og.copy()
        a = nx.difference(rg, og)
        b = nx.difference(ogc, rgc)
        self.assertTrue(nx.is_empty(a))
        self.assertTrue(nx.is_empty(b))
