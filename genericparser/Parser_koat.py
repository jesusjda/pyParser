from genericparser.Constraint_parser import ConstraintTreeTransformer
from genericparser import ParserInterface
from genericparser import constants
from lpi import Expression


class Parser_koat(ParserInterface):

    def parse(self, filepath, debug=False):
        """Parse .koat file

        :param filepath: Full path to file to be parsed.
        :type filepath: str
        :param debug: True to show debug information. Defaults to False
        :type debug: bool
        :returns: :obj:`pyParser.Cfg.Cfg` ControlFlowGraph.
        """
        with open(filepath) as file:
            fctext = file.read()
        return self.parse_string(fctext, debug=debug)

    def parse_string(self, cad, __=None, debug=False):
        import os
        grammarfile = os.path.join(os.path.dirname(__file__), "koat.g")
        with open(grammarfile, "r") as grammar:
            g = grammar.read()
        from lark.lark import Lark
        parser = Lark(g)
        return self.program2cfg(KoatTreeTransformer().transform(parser.parse(cad)))


class KoatTreeTransformer(ConstraintTreeTransformer):

    name = lambda self, node: str(node[0])
    number = lambda self, node: int(node[0])
    entry = lambda self, node: node[0]
    constraints = list
    variables = list
    noentry = lambda self, __: None

    def __init__(self):
        self.trs_count = 0
        self.variable_list = None
        self.pvars = None
        self.node_data = {}
        self.max_local_vars = 0

    def rules(self, node):
        trs = []
        for n in node:
            trs += n
        return trs

    def node(self, tnode):
        return tnode[0], tnode[1:]

    def rule(self, node):
        if len(node) == 3:
            left, right, cons = node
        elif len(node) == 2:
            left, right = node
            cons = []
        else:
            raise ValueError("too many tokens for rule")
        src_name, src_vars = left
        if src_name not in self.node_data:
            self.node_data[src_name] = {"Com": []}
        if len(right) > 1:
            self.node_data[src_name]["Com"].append(len(right))
        if self.variable_list is None:
            self.variable_list = [str(v) for v in src_vars]
            self.pvars = [v + "'" for v in self.variable_list]
        else:
            if len(self.variable_list) != len(src_vars):
                raise ValueError("variables are not uniform.")
            for v1, v2 in zip(self.variable_list, src_vars):
                if v1 != str(v2):
                    raise ValueError("variables are not uniform.")
        base_lvars = []
        base_linear = True
        for c in cons:
            if not c.is_linear():
                base_linear = False
            for v in c.get_variables():
                if v not in self.variable_list and v not in base_lvars:
                    base_lvars.append(v)
        trs = []
        for trg, trg_exp in right:
            if len(trg_exp) != len(self.variable_list):
                raise ValueError("node arguments doesn't match at transition: {} -> {}".format(src_name, trg))
            if trg not in self.node_data:
                self.node_data[trg] = {"Com": []}
            linear = base_linear
            lvars = list(base_lvars)
            final_cons = list(cons)
            for exp, pv in zip(trg_exp, self.pvars):
                if not exp.is_linear():
                    linear = False
                for v in exp.get_variables():
                    if v not in self.variable_list and v not in lvars:
                        lvars.append(v)
                final_cons.append(exp == Expression(pv))
            tr = {}
            tr["source"] = src_name
            tr["target"] = trg
            tr["name"] = "t" + str(self.trs_count)
            tr[constants.transition.constraints] = final_cons
            tr[constants.transition.localvariables] = lvars
            tr[constants.transition.islinear] = linear
            if len(lvars) > self.max_local_vars:
                self.max_local_vars = len(lvars)
            self.trs_count += 1
            trs.append(tr)
        return trs

    def right_hand(self, node):
        if len(node) > 1 and len(node) == node[0] + 1:
            return node[1:]
        elif len(node) == 1:
            return node
        else:
            raise ValueError("The number of target nodes are not correct")

    def start(self, node):
        program = {}
        program["goal"] = node[0]
        entry = node[1]
        program["transitions"] = node[3]
        # defined_vars = [str(v) for v in node[2]]
        program[constants.variables] = self.variable_list + self.pvars
        program["nodes"] = self.node_data
        if entry:
            program[constants.initnode] = entry
        else:
            program[constants.initnode] = program["transitions"][0]["source"]
        program["max_local_vars"] = self.max_local_vars
        return program
