from __future__ import unicode_literals, print_function
from arpeggio import *
from arpeggio import RegExMatch as _
from Cfg import *
from GenericParser import ParserInterface
from ppl import Variable
from ppl import Constraint_System
from LPi import C_Polyhedron


class Parser_mlc(ParserInterface):
    """MLC Parser
    """

    def parse(self, filepath, debug=False):
        """Parse .mlc file

        :param filepath: Full path to file to be parsed.
        :type filepath: str
        :param debug: True to show debug information. Defaults to False
        :type debug: bool
        :returns: :obj:`pyParser.Cfg.Cfg` ControlFlowGraph.
        """
        # Load test program from file
        test_program = open(filepath).read()
        # Parser instantiation
        parser = ParserPython(mlcprogram, mlccomment, debug=debug)
        parse_tree = parser.parse(test_program)
        cfg = visit_parse_tree(parse_tree, MlcProgramVisitor(debug=debug))

        return cfg


def mlccomment():
    return [_("#.*"), _("/\*[^(\*/)]*\*/")]


def mlcsymbol():
    return _(r"\w[\w0-9']*")


def mlcnumber():
    return _(r'\d*\.\d*|\d+')


def mlcfactor():
    return (Optional(["+", "-"]),
            [mlcnumber, ("(", mlcexpression, ")"), mlcsymbol])


def mlcterm():
    return mlcfactor, ZeroOrMore(["*", "/"], mlcfactor)


def mlcexpression():
    return mlcterm, ZeroOrMore(["+", "-"], mlcterm)


def mlcequation():
    return mlcexpression, ["<=", "=", ">=", ">", "<"], mlcexpression


def mlctransition():
    return (Kwd("!path"), OneOrMore(mlcequation))


def mlcvarlist():
    return Kwd("!vars"), OneOrMore(mlcsymbol)


def mlcpvarlist():
    return Kwd("!pvars"), OneOrMore(mlcsymbol)


def mlcprogram():
    return mlcvarlist, Optional(mlcpvarlist), OneOrMore(mlctransition), EOF


class MlcProgramVisitor(PTNodeVisitor):

    VarsList = []
    All_Vars = []
    PVars = False
    PVarsList = []
    startTr = False
    count = 0

    def convert(self, v):
        if not self.PVars:
            self.PVars = True
            self.All_Vars = self.VarsList + self.PVarsList
        if(isinstance(v, str) and (v in self.All_Vars)):
            return Variable(self.All_Vars.index(v))
        else:
            return v

    def visit_mlcsymbol(self, node, children):
        return str(node.value)

    def visit_mlcfactor(self, node, children):
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

    def visit_mlcterm(self, node, children):
        exp = self.convert(children[0])
        if(len(children) == 1):
            return exp
        if(children[1] == "*"):
            exp = exp * self.convert(children[2])
        else:
            exp = exp / self.convert(children[2])
        return exp

    def visit_mlcexpression(self, node, children):
        if self.debug:
            print("Exp {}.".format(node.value))
        exp = self.convert(children[0])
        for i in range(2, len(children), 2):
            if(children[i-1] == "-"):
                exp = exp - self.convert(children[i])
            elif(children[i-1] == "+"):
                exp = exp + self.convert(children[i])
        return exp

    def visit_mlcequation(self, node, children):
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

    def visit_mlctransition(self, node, children):
        if self.debug:
            print("Trans {}.".format(node.value))
        self.startTr = True
        tr_id = "t" + str(self.count)
        self.count += 1
        src = "n"
        trg = "n"
        cons = []
        for i in range(0, len(children)):
            cons.append(children[i])
        return tr_id, src, trg, cons

    def visit_mlcvarlist(self, node, children):
        if self.debug:
            print("varlist {}".format(children))
        self.VarsList = []
        self.PVarsList = []
        self.All_Vars = []
        for i in range(0, len(children)):
            if children[i] in self.All_Vars:
                raise Exception("Name repeated : "+children[i])
            self.VarsList.append(str(children[i]))
            self.All_Vars.append(str(children[i]))
            self.PVarsList.append(str(children[i]+"\'"))

        self.PVars = False
        return False

    def visit_mlcpvarlist(self, node, children):
        if self.debug:
            print("pvarlist {}".format(children))
        self.PVars = False
        self.PVarsList = []
        for i in range(0, len(children)):
            self.PVarsList.append(str(children[i]))
        self.startTr = False

        return False

    def visit_mlcprogram(self, node, children):
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
            G.add_edge(tr_id, src, trg, tr_polyhedron=tr_poly)
        G.add_var_name(self.All_Vars)
        return G

    def visit_mlcnumber(self, node, children):
        if self.debug:
            print("Converting {}.".format(node.value))
        return float(node.value)
