from __future__ import unicode_literals, print_function
import os
import sys
from arpeggio import *
from arpeggio import RegExMatch as _
import ppl as LP
from Cfg import *


def parse(filepath, debug=False):
    """Parse .fc file

   :param filepath: Full path to file to be parsed.
   :type filepath: str
   :param debug: True to show debug information. Defaults to False
   :type debug: bool
   :returns: :obj:`pyParser.Cfg.Cfg` Cfg obj with the program ControlFlowGraph.
    """
    # Load test program from file
    test_program = open(filepath).read()
    # Parser instantiation
    parser = ParserPython(fcprogram, fccomment, debug=debug)
    parse_tree = parser.parse(test_program)
    cfg = visit_parse_tree(parse_tree, FcProgramVisitor(debug=debug))
    return cfg


def fccomment():
    return [_("//.*"), _("/\*[^(\*/)]*\*/"),
            (Kwd(".itrans"), _(r'[^\}]*'), "}")]


def fcsymbol():
    return _(r"\w+")


def fcnumber():
    return _(r'\d*\.\d*|\d+')


def fcfactor():
    return (Optional(["+", "-"]),
            [fcnumber, ("(", fcexpression, ")"), fcsymbol])


def fcterm():
    return fcfactor, ZeroOrMore(["*", "/"], fcfactor)


def fcexpression():
    return OneOrMore(fcterm, sep="+")


def fcequation():
    return fcexpression, ["<=", "=", ">=", ">", "<"], fcexpression


def fctransition():
    return (Kwd(".trans"), fcsymbol, ":", fcsymbol, "->", fcsymbol,
            "{", OneOrMore(fcequation, sep=","), "}")


def fcvarlist():
    return Kwd(".vars"), "{", OneOrMore(fcsymbol, sep=","), "}"


def fcpvarlist():
    return Kwd(".pvars"), "{", OneOrMore(fcsymbol, sep=","), "}"


def fcprogram():
    return fcvarlist, fcpvarlist, OneOrMore(fctransition), EOF


class FcProgramVisitor(PTNodeVisitor):

    def convert(self, v):
        if(isinstance(v, float)):
            return v
        elif(isinstance(v, str) and (v in self.All_Vars)):
            return LP.Variable(self.All_Vars.index(v))
        else:
            return v

    def visit_fcsymbol(self, node, children):
        return node.value

    def visit_fcfactor(self, node, children):
        if self.debug:
            print("Factor {}.".format(node.value))
        exp = 0
        if(len(node) == 1):
            exp = self.convert(children[0])
        elif(len(node) == 2):
            if(node[0] == '-'):
                exp = - self.convert(children[1])
            else:
                exp = self.convert(children[1])
        elif(node[0] == '('):
            exp = (self.convert(children[0]))
        return exp

    def visit_fcterm(self, node, children):
        exp = self.convert(children[0])
        if(len(children) == 1):
            return exp
        if(children[1] == "*"):
            exp = exp * self.convert(children[2])
        else:
            exp = exp / self.convert(children[2])
        return exp

    def visit_fcexpression(self, node, children):
        if self.debug:
            print("Exp {}.".format(node.value))
        exp = self.convert(children[0])
        for i in range(2, len(children), 2):
            if(children[i-1] == "-"):
                exp = exp - self.convert(children[i])
            elif(children[i-1] == "+"):
                exp = exp + self.convert(children[i])
        return exp

    def visit_fcequation(self, node, children):
        if self.debug:
            print("Eq {}.".format(node.value))
        exp = children[0]
        if(children[1] == "<"):
            exp = (exp < children[2])
        elif(children[1] == ">"):
            exp = (exp > children[2])
        elif(children[1] == "<="):
            exp = (exp <= children[2])
        elif(children[1] == ">="):
            exp = (exp >= children[2])
        elif(children[1] == "="):
            exp = (exp == children[2])
        return exp

    def visit_fctransition(self, node, children):
        if self.debug:
            print("Trans {}.".format(node.value))
        tr_id = children[0]
        src = children[1]
        trg = children[2]
        cons = []
        E = Edge(tr_id, src, trg)
        for i in range(3, len(children), 2):
            cons.append(children[i])
        return tr_id, src, trg, cons

    def visit_fcvarlist(self, node, children):
        if self.debug:
            print("varlist {}".format(children))
        self.All_Vars = []
        for i in range(0, len(children), 2):
            if children[i] in self.All_Vars:
                raise Exception("Name repeated : "+children[i])
            self.All_Vars.append(children[i])
        return True

    def visit_fcpvarlist(self, node, children):
        if self.debug:
            print("pvarlist {}".format(children))
        for i in range(0, len(children), 2):
            self.All_Vars.append(children[i])
        return True

    def visit_fcprogram(self, node, children):
        if self.debug:
            print("Program {}.".format(node.value))
        G = Cfg()
        Trans = []
        Vars = children[0]
        PVars = children[1]
        for i in range(2, len(children)):
            tr_id, src, trg, cons = children[i]
            G.add_edge(Edge(tr_id, src, trg, cons))
        return G

    def visit_fcnumber(self, node, children):
        if self.debug:
            print("Converting {}.".format(node.value))
        return float(node.value)


def _main():
    # In debug mode dot (graphviz) files for parser model
    # and parse tree will be created for visualization.
    # Checkout current folder for .dot files.
    current_dir = os.path.dirname(__file__)
    filename = "examples/example.fc"
    filepath = os.path.join(current_dir, filename)
    a = parse(filepath, False)
    print(a)

if __name__ == "__main__":
    _main()
