from __future__ import unicode_literals, print_function
from arpeggio import *
from arpeggio import RegExMatch as _
from ppl import Variable
from ppl import Constraint_System
from ppl import Linear_Expression
from lpi import C_Polyhedron
from Cfg import *
from genericparser import ParserInterface


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
        lines = open(filepath).readlines()
        # INTERNAL ATTR
        VarList = []
        PVarList = []
        self.VARS = []
        lines = self.remove_comments(lines)
        it = 0
        # !vars
        if lines[it] != "!vars":
            raise Exception("Expecting \"!vars\"")
        it += 1
        # x y z
        for var in lines[it].split():
            if len(var) <= 0:
                continue
            if var in VarList:
                raise Exception("Name repeated : " + var)
            VarList.append(var)
            PVarList.append(var + "\'")
        it += 1
        # !pvars
        if lines[it] == "!pvars":
            it += 1
            PVarList = []
            # x' y' z'
            for var in lines[it].split():
                if len(var) <= 0:
                    continue
                if var in VarList or var in PVarList:
                    raise Exception("Name repeated : " + var)
                PVarList.append(var)
            it += 1
        self.VARS = VarList + PVarList

        tr_id = 0
        G = Cfg()
        # !path
        while it < len(lines):
            tr, it = self.visit_transition(lines, it)
            tr_poly = C_Polyhedron(Constraint_System(tr), len(self.VARS))
            G.add_edge("t" + str(tr_id), "n", "n", tr_polyhedron=tr_poly)
            tr_id += 1

        G.add_var_name(self.VARS)
        return G

    def visit_expr(self, line):
        return self.visit_expression(line)

    def visit_expression(self, line):
        options = ["([a-zA-Z]+[a-zA-Z0-9]*)", "[0-9]+",
                   "\+", "\-", "\(", "\)", "\/", "\*"]
        e = [line]
        for rep in options:
            nep = e
            e = []
            for s in nep:
                if not(s is None):
                    e += re.split("("+rep+")+", s)
        e = [a for a in e if a != '']
        pass

    def visit_equation(self, line):
        line = line.strip()
        return self.parseEq(line)

    def visit_transition(self, lines, it):
        if lines[it] != "!path":
            raise Exception("Expecting \"!path\"")
        it += 1
        EXPS = []
        while it < len(lines) and lines[it] != "!path":
            exp = self.visit_equation(lines[it])
            EXPS.append(exp)
            it += 1
        return EXPS, it

    def remove_comments(self, lines):
        L = []
        multicomment = False
        for l in lines:
            laux, multicomment = self.remove_comment(l, multicomment)
            laux = laux.strip()
            if len(laux) > 0:
                L.append(laux)
        return L

    def remove_comment(self, line, multicomment):
        multi = multicomment
        if multicomment:
            pos = line.find("*/")
            if pos >= 0:
                line = line[(pos + 2)::]
                multi = False
            else:
                line = ""
        pos = line.find("#")
        if pos >= 0:
            line = line[0:pos]
        pos = line.find("/*")
        if pos >= 0:
            line = line[0:pos]
            multi = True
        return line.replace("\n", ""), multi

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
        else:
            return v

    def visit_eqsymbol(self, node, children):
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

    def visit_eqterm(self, node, children):
        exp = self.convert(children[0])
        if(len(children) == 1):
            return exp
        if isinstance(children[1], (str, unicode)):
            if(children[1] == "/"):
                exp = exp / self.convert(children[2])
            else:
                exp = exp * self.convert(children[2])
        else:
            exp = exp * children[1]
        return exp

    def visit_eqexpression(self, node, children):
        exp = self.convert(children[0])
        for i in range(2, len(children), 2):
            if(children[i-1] == "-"):
                exp = exp - self.convert(children[i])
            elif(children[i-1] == "+"):
                exp = exp + self.convert(children[i])
        return exp

    def visit_eqequation(self, node, children):
        exp = children[0]
        if(children[1] == "<"):
            exp = (exp < children[2])
        elif(children[1] == ">"):
            exp = (exp > children[2])
        elif(children[1] == "<=" or children[1] == "=<"):
            exp = (exp <= children[2])
        elif(children[1] == ">=" or children[1] == "=>"):
            exp = (exp >= children[2])
        elif(children[1] == "=" or children[1] == "=="):
            exp = (exp == children[2])
        return exp

    def visit_eqnumber(self, node, children):
        return float(node.value)

