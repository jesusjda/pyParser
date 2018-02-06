from __future__ import unicode_literals, print_function

from arpeggio import EOF
from arpeggio import Kwd
from arpeggio import OneOrMore
from arpeggio import Optional
from arpeggio import PTNodeVisitor
from arpeggio import ParserPython
from arpeggio import RegExMatch as _
from arpeggio import ZeroOrMore
from arpeggio import visit_parse_tree
from lpi import C_Polyhedron
from ppl import Constraint_System
from ppl import Linear_Expression
from ppl import Variable

from . import ParserInterface
from .Cfg import Cfg


class Parser_fc(ParserInterface):
    """Fc Parser
    """

    def parse(self, filepath, debug=False):
        """Parse .fc file

        :param filepath: Full path to file to be parsed.
        :type filepath: str
        :param debug: True to show debug information. Defaults to False
        :type debug: bool
        :returns: :obj:`pyParser.Cfg.Cfg` ControlFlowGraph.
        """
        # Load test program from file
        test_program = open(filepath).read()
        # Parser instantiation
        parser = ParserPython(fcprogram, fccomment, debug=debug)
        parse_tree = parser.parse(test_program)
        cfg = visit_parse_tree(parse_tree, FcProgramVisitor(debug=debug))

        return cfg

    def parse_string(self, string, _=None, debug=False):
        parser = ParserPython(fcprogram, fccomment, debug=debug)
        parse_tree = parser.parse(str(string))
        cfg = visit_parse_tree(parse_tree, FcProgramVisitor(debug=debug))
        return cfg

    def parseEq(self, line, Vars):
        parser = ParserPython(fcequation)
        parse_tree = parser.parse(line)
        FCP = FcProgramVisitor()
        FCP.All_Vars = Vars
        FCP.PVars = True
        eq = visit_parse_tree(parse_tree, FcProgramVisitor())
        return eq


def fccomment():
    return [_("//.*"), _("/\*[^(\*/)]*\*/"),
            (Kwd(".itrans"), _(r'[^\}]*'), "}")]


def fcsymbol():
    return _(r"[\w_][\w0-9'\^_\!]*")


def fcnumber():
    return _(r'\d*\.\d*|\d+')


def fcfactor():
    return (Optional(["+", "-"]),
            [fcnumber, ("(", fcexpression, ")"), fcsymbol])


def fcterm():
    return fcfactor, ZeroOrMore(["*", "/"], fcfactor)


def fcexpression():
    return fcterm, ZeroOrMore(["+", "-"], fcterm)


def fcequation():
    return fcexpression, ["<=", "=", ">=", ">", "<"], fcexpression


def fctransition():
    return (Kwd(".trans"), fcsymbol, ":", fcsymbol, "->", fcsymbol,
            "{", OneOrMore(fcequation, sep=","), "}")


def fcvarlist():
    return Kwd(".vars"), "{", ZeroOrMore(fcsymbol, sep=","), "}"


def fcpvarlist():
    return Kwd(".pvars"), "{", ZeroOrMore(fcsymbol, sep=","), "}"


def fcinitnode():
    return Kwd(".initnode"), ":", fcsymbol


def fcprogram():
    return (fcvarlist, Optional(fcpvarlist), Optional(fcinitnode),
            OneOrMore(fctransition), EOF)


class FcProgramVisitor(PTNodeVisitor):

    VarsList = []
    All_Vars = []
    PVars = False
    PVarsList = []
    startTr = False
    init_node = None
    no_linear = False
    no_linear_tr = False

    def convert(self, v):
        if not self.PVars:
            self.PVars = True
            self.All_Vars = self.VarsList + self.PVarsList
        if(isinstance(v, str) and (v in self.All_Vars)):
            return Variable(self.All_Vars.index(v))
        else:
            return v

    def visit_fcsymbol(self, node, _):
        return str(node.value)

    def visit_fcfactor(self, node, children):
        if self.no_linear:
            return 0
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

    def visit_fcterm(self, _, children):
        if self.no_linear:
            return 0
        exp = self.convert(children[0])
        if(len(children) == 1):
            return exp
        try:
            if(children[1] == "*"):
                exp = exp * self.convert(children[2])
            else:
                exp = exp / self.convert(children[2])
        except TypeError:
            self.no_linear = True
            self.no_linear_tr = True
        return exp

    def visit_fcexpression(self, node, children):
        if self.no_linear:
            return 0
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
        exp = Linear_Expression(children[0])
        c2 = Linear_Expression(children[2])
        if self.no_linear:
            exp = Linear_Expression(0)
            c2 = Linear_Expression(0)
            self.no_linear = False
            return exp == c2
        if(children[1] == "<"):
            exp = (exp <= (c2-1))
        elif(children[1] == ">"):
            exp = (exp >= (c2+1))
        elif(children[1] == "<="):
            exp = (exp <= c2)
        elif(children[1] == ">="):
            exp = (exp >= c2)
        elif(children[1] == "=" or children[1] == "=="):
            exp = (exp == c2)
        return exp

    def visit_fctransition(self, node, children):
        if self.debug:
            print("Trans {}.".format(node.value))
        self.startTr = True
        tr_id = children[0]
        src = children[1]
        if self.init_node is None:
            self.init_node = src
        trg = children[2]
        cons = []
        for i in range(3, len(children), 2):
            cons.append(children[i])
        linear = not self.no_linear_tr
        self.no_linear_tr = False
        return tr_id, src, trg, cons, linear

    def visit_fcvarlist(self, _, children):
        if self.debug:
            print("varlist {}".format(children))
        self.VarsList = []
        self.PVarsList = []
        self.All_Vars = []
        self.PVars = False
        for i in range(0, len(children), 2):
            if children[i] in self.All_Vars:
                raise Exception("Name repeated : "+children[i])
            self.VarsList.append(str(children[i]))
            self.All_Vars.append(str(children[i]))
            self.PVarsList.append(str(children[i]+"\'"))

        return False

    def visit_fcpvarlist(self, _, children):
        if self.debug:
            print("pvarlist {}".format(children))
        self.PVars = False
        self.PVarsList = []
        self.startTr = False
        for i in range(0, len(children), 2):
            self.PVarsList.append(str(children[i]))
        return False

    def visit_fcinitnode(self, _, children):
        if self.debug:
            print("initnode {}".format(children))
        self.init_node = children[0]
        return False

    def visit_fcprogram(self, node, children):
        if self.debug:
            print("Program {}.".format(node.value))
        G = Cfg()
        children[0]
        children[1]
        Dim = len(self.All_Vars)
        for i in range(1, len(children)):
            if not children[i]:
                continue
            tr_id, src, trg, cons, linear = children[i]
            tr_poly = C_Polyhedron(Constraint_System(cons), Dim)
            G.add_edge(tr_id, src, trg,
                       tr_polyhedron=tr_poly, line=1, linear=linear)
        G.add_var_name(self.All_Vars)
        G.set_init_node(self.init_node)
        return G

    def visit_fcnumber(self, node, _):
        if self.debug:
            print("Converting {}.".format(node.value))
        return float(node.value)