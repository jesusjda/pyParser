from __future__ import unicode_literals, print_function

from arpeggio import Optional
from arpeggio import PTNodeVisitor
from arpeggio import ParserPython
from arpeggio import RegExMatch as _
from arpeggio import ZeroOrMore
from arpeggio import visit_parse_tree
from genericparser.expressions import inequation

def parseEq(self, line):
    parser = ParserPython(eqequation)
    parse_tree = parser.parse(line)
    FCP = EquationVisitor()
    FCP.All_Vars = self.VARS
    eq = visit_parse_tree(parse_tree, FCP)
    return eq


def eqsymbol():
    return _(r"\w[\w0-9']*")


def eqnumber():
    return _(r'\d*\.\d*|\d+')


def eqsign():
    return (Optional(["+", "-"]), eqfactor)


def eqfactor():
    return [(eqnumber, Optional(("/", eqnumber))),
            ("(", eqexpression, ")"), eqsymbol]


def eqterm():
    return eqsign, ZeroOrMore([("*", eqsign), (eqfactor)])


def eqexpression():
    return eqterm, ZeroOrMore(["+", "-"], eqterm)


def eqequation():
    return (eqexpression,
            ["<=", "=>", "=<", ">=", "=", "==", ">", "<"], eqexpression)


class EquationVisitor(PTNodeVisitor):

    All_Vars = []

    def convert(self, v):
        if(isinstance(v, str) and (v in self.All_Vars)):
            return Variable(self.All_Vars.index(v))
        elif isinstance(v, (int, float)):
            return Linear_Expression(v)
        else:
            return v

    def visit_eqsymbol(self, node, _):
        return str(node.value)

    def visit_eqfactor(self, node, children):
        exp = 0
        if isinstance(children[0], float):
            exp = children[0]
            if len(children) > 1:
                exp = exp / children[1]
        elif node[0] == '(':
            exp = exp + (children[0])
        else:
            exp = exp + self.convert(children[0])
        return exp

    def visit_eqsign(self, node, children):
        exp = 0
        if len(node) == 1:
            exp = exp + children[0]
        else:
            if node[0] == '-':
                exp = exp - children[1]
            else:
                exp = exp + children[2]
        return exp

    def visit_eqterm(self, _, children):
        exp = self.convert(children[0])
        if(len(children) == 1):
            return exp
        if isinstance(children[1], (str)):
            if(children[1] == "/"):
                exp = exp / self.convert(children[2])
            else:
                exp = exp * self.convert(children[2])
        else:
            exp = exp * children[1]
        return exp

    def visit_eqexpression(self, _, children):
        exp = self.convert(children[0])
        for i in range(2, len(children), 2):
            if(children[i-1] == "-"):
                exp = exp - self.convert(children[i])
            elif(children[i-1] == "+"):
                exp = exp + self.convert(children[i])
        return exp

    def visit_eqequation(self, _, children):
        return inequation(children[0], children[2], children[1])

    def visit_eqnumber(self, node, _):
        return float(node.value)
