from __future__ import unicode_literals, print_function
from arpeggio import *
from arpeggio import RegExMatch as _
from ppl import Variable
from ppl import Constraint_System
from lpi import C_Polyhedron
from .Cfg import Cfg
from . import ParserInterface
from termination.output import Output_Manager as OM


class Parser_t2(ParserInterface):
    """T2 Parser
    """

    def parse(self, filepath, debug=False):
        """Parse .t2 file

        :param filepath: Full path to file to be parsed.
        :type filepath: str
        :param debug: True to show debug information. Defaults to False
        :type debug: bool
        :returns: :obj:`pyParser.Cfg.Cfg` ControlFlowGraph.
        """
        raise Exception("NOT IMPLEMENTED YET")
        # Load test program from file
        test_program = open(filepath).read()
        # Parser instantiation
        parser = ParserPython(t2program, t2comment, debug=debug)
        parse_tree = parser.parse(test_program)
        cfg = visit_parse_tree(parse_tree, T2ProgramVisitor(debug=debug))
        return cfg


def t2comment():
    return _("\%.*")


def t2symbol():
    return _(r"[\w\_][\w0-9\_']*")


def t2number():
    return _(r'\d*\.\d*|\d+')


def t2factor():
    return (Optional(["+", "-"]),
            [t2number, ("(", t2expression, ")"), t2symbol])


def t2term():
    return t2factor, ZeroOrMore(["*", "/"], t2factor)


def t2expression():
    return t2term, ZeroOrMore(["+", "-"], t2term)


def t2equation():
    return t2expression, ["<=", "=", ">=", ">", "<"], t2expression


def t2assume():
    return Kwd('assume'), "(", OneOrMore(t2equation, sep="&&"), ")"


def t2asignation():
    return t2symbol, ":=", [t2expression, Kwd("nondet()")]


def t2instruction():
    return [t2asignation, t2assume], ";"


def t2transition():
    return (Kwd('FROM'), ":", t2number, ";",
            OneOrMore(t2instruction, sep=";"),
            Kwd('TO'), ":", t2number, ";")


def t2start():
    return Kwd("START"), ":", t2number, ";"


def t2program():
    return (t2start, oneOrMore(t2transition)), EOF


class T2ProgramVisitor(PTNodeVisitor):

    VarsList = []
    All_Vars = []
    PVars = False
    PVarsList = []
    startTr = False

    def convert(self, v, VAR=False):
        return v

    def visit_t2symbol(self, node, children):
        return str(node.value)

    def visit_t2factor(self, node, children):
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

    def visit_t2term(self, node, children):
        exp = self.convert(children[0])
        if(len(children) == 1):
            return exp
        if(children[1] == "*"):
            exp = exp * self.convert(children[2])
        else:
            exp = exp / self.convert(children[2])
        return exp

    def visit_t2expression(self, node, children):
        if self.debug:
            print("Exp {}.".format(node.value))
        exp = self.convert(children[0])
        for i in range(2, len(children), 2):
            if(children[i-1] == "-"):
                exp = exp - self.convert(children[i])
            elif(children[i-1] == "+"):
                exp = exp + self.convert(children[i])
        return exp

    def visit_t2equation(self, node, children):
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

    def visit_t2transition(self, node, children):
        OM.printif(2, node)
        if self.debug:
            print("Trans {}.".format(node.value))
        self.startTr = True
        tr_id = children[0]
        src = children[1]
        trg = children[2]
        cons = []
        for i in range(3, len(children), 2):
            cons.append(children[i])
        return tr_id, src, trg, cons

    def visit_t2varlist(self, node, children):
        if self.debug:
            print("varlist {}".format(children))
        self.VarsList = []
        self.PVarsList = []
        self.All_Vars = []
        for i in range(0, len(children), 2):
            if children[i] in self.All_Vars:
                raise Exception("Name repeated : "+children[i])
            self.VarsList.append(str(children[i]))
            self.All_Vars.append(str(children[i]))
            self.PVarsList.append(str(children[i]+"\'"))

        self.PVars = False
        return False

    def visit_t2pvarlist(self, node, children):
        if self.debug:
            print("pvarlist {}".format(children))
        self.PVars = False
        self.PVarsList = []
        for i in range(0, len(children), 2):
            self.PVarsList.append(str(children[i]))
        self.startTr = False
        return False

    def visit_t2program(self, node, children):
        if self.debug:
            print("Program {}.".format(node.value))
        G = Cfg()
        Trans = []
        children[0]
        children[1]
        Dim = len(self.All_Vars)
        for i in range(1, len(children)):
            if not children[i]:
                continue
            tr_id, src, trg, cons = children[i]
            tr_poly = C_Polyhedron(Constraint_System(cons), Dim)
            G.add_edge(tr_id, src, trg,
                       tr_polyhedron=tr_poly, line=1)
        G.add_var_name(self.All_Vars)
        return G

    def visit_t2number(self, node, children):
        if self.debug:
            print("Converting {}.".format(node.value))
        return float(node.value)
