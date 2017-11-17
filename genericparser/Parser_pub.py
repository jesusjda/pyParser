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
import re
from z3 import *
from . import ParserInterface


class Parser_pub(ParserInterface):
    """Pub Parser
    """

    def parse(self, filepath, debug=True):
        """Parse .pub file

        :param filepath: Full path to file to be parsed.
        :type filepath: str
        :param debug: True to show debug information. Defaults to False
        :type debug: bool
        :returns: :obj:`pyParser.Cfg.Cfg` ControlFlowGraph.
        """
        # Load test program from file
        test_program = open(filepath).read()
        # Parser instantiation
        parser = ParserPython(pubprogram, pubcomment, debug=debug)
        parse_tree = parser.parse(test_program)
        cfg = visit_parse_tree(parse_tree, PubProgramVisitor(debug=debug))

        return cfg

    def parse_string(self, string, debug=False):
        parser = ParserPython(pubprogram, pubcomment, debug=debug)
        parse_tree = parser.parse(string)
        cfg = visit_parse_tree(parse_tree, PubProgramVisitor(debug=debug))
        return cfg

    def parseEq(self, line, Vars):
        parser = ParserPython(pubequation)
        parse_tree = parser.parse(line)
        PUBP = PubProgramVisitor()
        PUBP.All_Vars = Vars
        PUBP.PVars = True
        eq = visit_parse_tree(parse_tree, PubProgramVisitor())
        return eq


def pubcomment():
    return [_("//.*"), _("/\*[^(\*/)]*\*/"),
            (Kwd(".iphi"), _(r'[^\}]*'), "}")]


def pubnumber():
    return _(r'\d*\.\d*|\d+')


def pubvar():
    return _(r"\w+")


def pubsymbol():
    return _(r"\w+[0-9]*")


def pubfactor():
    return (Optional(["+", "-"]),
            [pubnumber, ("(", pubexpression, ")"), pubsymbol])


def pubterm():
    return pubfactor, ZeroOrMore(["*", "/"], pubfactor)


def pubexpression():
    return pubterm, ZeroOrMore(["+", "-"], pubterm)


def pubequation():
    return pubexpression, ["=", "==", ">="], pubexpression


def pubconstr():
    return (Kwd(".constraints"), "{", OneOrMore(pubequation, sep=";"), "}")


def pubf():
    return Kwd(".f"), "->", pubequation


def pubphi():
    return (Kwd(".phi"), # pubsymbol,
            "{", pubconstr, ";", OneOrMore(pubf, sep=';'), "}")


def pubvarlist():
    return Kwd(".vars"), "{", OneOrMore(pubvar, sep=";"), "}"


def pubprogram():
    return (pubvarlist, OneOrMore(pubphi), EOF)


class PubProgramVisitor(PTNodeVisitor):

    program = {}
    varlistdone = False
    actual_f = []

    def convert(self, v):
        if isinstance(v, float):
            return Real(str(v)), None
        else:
            name = re.sub(r"[0-9]", "", v)
            if not(name in self.program["vars_name"]) and name != "a":
                raise Exception("Variable ("+v+") does not exists.")
            if name == "a":
                return Real(v), None
            if not(v in self.program["vars_order"]):
                self.program["vars_order"].append(v)
            return Real(1), self.program["vars_order"].index(v)

    def idx_of_var(self, variable):
        if not(variable in self.program["vars_order"]):
            self.program["vars_order"].append(variable)
        return self.program["vars_order"].index(variable)

    def visit_pubnumber(self, node, children):
        if self.debug:
            print("Converting {}.".format(node.value))
        return float(node.value)

    def visit_pubvar(self, node, children):
        return str(node.value)

    def visit_pubsymbol(self, node, children):
        return str(node.value)

    def visit_pubfactor(self, node, children):
        if self.debug:
            print("Factor {}.".format(node.value))
        exp = RealVal(1)
        if(len(node) == 1):
            exp, var_idx = self.convert(children[0])
        elif(len(node) == 2):
            if(node[0] == '-'):
                exp, var_idx = self.convert(children[1])
                exp = simplify((- exp))
            else:
                exp, var_idx = self.convert(children[1])
        elif(node[0] == '('):
            cffs, ind = children[0]
            for c in cffs:
                if c != 0:
                    raise Exception("No Linear 2")
            exp = ind
            var_idx = None
        return exp, var_idx

    def visit_pubterm(self, node, children):
        coeff = RealVal(1)
        variable = None
        for i in range(0, len(children), 2):
            exp, var_idx = children[i]
            if var_idx is not None:
                if variable is None:
                    variable = var_idx
                else:
                    raise Exception("No linear")
            if var_idx is not None and children[i-1] == "/":
                raise Exception("div variable")
            if(i > 0 and children[i-1] == "/"):
                coeff *= Q(1, exp)
            else:
                coeff *= exp
        return (simplify(coeff), variable)

    def visit_pubexpression(self, node, children):
        if self.debug:
            print("Exp {}.".format(node.value))
        coeffs = []
        indep = RealVal(0)
        for i in range(0, len(children), 2):
            c, var_idx = children[i]
            if var_idx is None:
                if(i > 0 and children[i-1] == "-"):
                    indep = simplify(indep - c)
                else:
                    indep += c
            else:
                for _ in range(len(coeffs), var_idx+1):
                    coeffs.append(RealVal(0))
                if(i > 0 and children[i-1] == "-"):
                    coeffs[var_idx] -= c
                else:
                    coeffs[var_idx] += c
        return (coeffs, indep)

    def visit_pubequation(self, node, children):
        if self.debug:
            print("Eq {}.".format(node.value))
        coeffs = []
        symbol = ""
        if(children[1] == "<="):
            izq, i_indep = children[2]
            der, d_indep = children[0]
            symbol = ">="
        elif(children[1] == ">="):
            izq, i_indep = children[0]
            der, d_indep = children[2]
            symbol = ">="
        elif(children[1] == "=" or children[1] == "=="):
            izq, i_indep = children[0]
            der, d_indep = children[2]
            symbol = "=="
        else:
            raise Exception("ERROR")
        for i in range(len(self.program["vars_order"])):
            iz = RealVal(0)
            if i < len(izq):
                iz = simplify(izq[i])
            de = RealVal(0)
            if i < len(der):
                de = simplify(der[i])
            coeffs.append(simplify(iz - de))
        indep = simplify(d_indep - i_indep)
        return {"coeffs": coeffs, "symbol": symbol,
                "independent": indep}

    def visit_pubf(self, node, children):
        if self.debug:
            print("F {}.".format(node.value))
        return children[0]

    def visit_pubconstr(self, node, children):
        if self.debug:
            print("constr {}.".format(node.value))
        constraint = {"matrix": [],
                      "symbol": [],
                      "independent": []
                      }
        for i in range(0, len(children)):
            c = children[i]
            if c == ";":
                continue
            constraint["matrix"].append(c["coeffs"])
            constraint["symbol"].append(c["symbol"])
            constraint["independent"].append(simplify(c["independent"]))
        return constraint

    def visit_pubphi(self, node, children):
        if self.debug:
            print("Phi {}.".format(node.value))
        phi = {}
        # phi["name"] = children[0]
        phi["constraints"] = children[0]
        phi["fs"] = []
        for i in range(1, len(children)):
            phi["fs"].append(children[i])
        return phi

    def visit_pubvarlist(self, node, children):
        if self.debug:
            print("varlist {}".format(children))
        VarsList = []
        for i in range(0, len(children), 2):
            variable = children[i]
            if variable in VarsList:
                raise Exception("Name repeated : " + variable)
            VarsList.append(variable)
        self.program = {}
        self.program["vars_name"] = VarsList
        self.program["vars_order"] = VarsList
        return VarsList

    def visit_pubprogram(self, node, children):
        if self.debug:
            print("Program {}.".format(node.value))
        children[0]
        self.program["phis"] = []
        for i in range(1, len(children)):
            self.program["phis"].append(children[i])
        return self.program
