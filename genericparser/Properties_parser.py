from genericparser.Constraint_parser import ConstraintTreeTransformer


class Parser_Properties:

    def parse(self, filepath, debug=False):
        with open(filepath) as file:
            fctext = file.read()
        return self.parse_string(fctext, debug=debug)

    def parse_string(self, cad, __=None, debug=False):
        import os
        grammarfile = os.path.join(os.path.dirname(__file__), "fc.g")
        with open(grammarfile, "r") as grammar:
            g = grammar.read()
        from lark.lark import Lark
        parser = Lark(g, parser='lalr')
        return PropsTreeTransformer().transform(parser.parse(cad))


class PropsTreeTransformer(ConstraintTreeTransformer):

    list = list
    lvars = list
    pair = tuple
    null = lambda self, __: None
    true = lambda self, __: True
    false = lambda self, __: False
    key = lambda self, node: str(node[0])
    namekey = lambda self, node: str(node[0])
    lvarskey = lambda self, node: str(node[0])
    name = lambda self, node: str(node[0])

    def dict(self, node):
        keys = []
        for n in node:
            k, __ = n
            if k in keys:
                raise ValueError("Duplicate key: {}".format(k))
            keys.append(k)
        return dict(node)

    def start(self, node):
        return node[0]
