from lpi.Expressions import ExprTerm
from lpi.Expressions import Expression
from lark import Transformer
from . import ParserInterface


class Parser_Constraint(ParserInterface):

    def parse(self, filepath, debug=False):
        """Parse constraint

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
        grammarfile = os.path.join(os.path.dirname(__file__), "constraint.g")
        with open(grammarfile, "r") as grammar:
            g = grammar.read()
        from lark.lark import Lark
        parser = Lark(g)
        return ConstraintTreeTransformer().transform(parser.parse(cad))


class ConstraintTreeTransformer(Transformer):
    """To use this parser, you must add ConstraintTreeTransformer
    as parent of your transformer. Also, your syntax should
    include:

    CMP: "<="|"=>"|"=<"|"=="|">="|">"|"<"|"="
    SUM: "+" | "-"
    MUL: "*" | "/"

    CNAME: ("_"|LETTER) ("_"|LETTER|DIGIT|"'"|"^"|"!")*

    term: [SUM] NUMBER | [SUM] CNAME | "(" expression ")"
    factor: term (MUL term)*
    expression:  factor (SUM factor)*

    constraint: expression CMP expression
    """
    def start(self, node):
        return node[0]

    def constraint(self, node):
        e1 = node[0]
        e2 = node[2]

        comp = node[1]
        if(comp == "<"):
            exp = (e1 < (e2))
        elif(comp == ">"):
            exp = (e1 > (e2))
        elif(comp == "<=" or comp == "=<"):
            exp = (e1 <= e2)
        elif(comp == ">=" or comp == "=>"):
            exp = (e1 >= e2)
        elif(comp == "=" or comp == "=="):
            exp = (e1 == e2)
        else:
            raise ValueError("Expecting compare op getting {}".format(comp))
        return exp

    def expression(self, node):
        exp = node[0]
        for i in range(2, len(node), 2):
            op = node[i - 1]
            e2 = node[i]
            if op == "+":
                exp = exp + e2
            elif op == "-":
                exp = exp - e2
        return exp

    def factor(self, node):
        exp = node[0]
        for i in range(2, len(node), 2):
            op = node[i - 1]
            e2 = node[i]
            if op == "*":
                exp = exp * e2
            elif op == "/":
                exp = exp / e2
        return exp

    def term(self, node):
        if len(node) == 2:
            val_pos = 1
        else:
            val_pos = 0
        if isinstance(node[val_pos], Expression):
            val = node[val_pos]
        else:
            val = ExprTerm(str(node[val_pos]))
        if len(node) == 2 and str(node[0]) == "-":
            return ExprTerm(0) - val
        else:
            return val
