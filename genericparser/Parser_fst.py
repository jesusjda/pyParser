
from genericparser import ParserInterface
from genericparser import boolexp
from genericparser.Cfg import Cfg
from lpi import C_Polyhedron
from ppl import Constraint
from ppl import Constraint_System
from ppl import Linear_Expression
from ppl import Variable
from pyleri import (
    Tokens,
    Optional,
    Repeat,
    Choice,
    Grammar,
    Keyword,
    Regex,
    Sequence,
    List,
    Ref)


def json_key(name, value):
    return Sequence(name, ":", value)


def json_dict(name, value):
    return Sequence("{", List(json_key(name, value)), "}")


def json_list(value):
    return Sequence("[", List(value), "]")


def json_dict_list(value):
    return Sequence("{", List(value), "}")


# Create a Grammar Class to define your language
class FST_Grammar(Grammar):
    ks_equa = Tokens("<= =< < >= => > = ==")
    r_string = Regex('(")(?:(?=(\\\?))\\2.)*?\\1')
    k_true = Keyword('true')
    k_false = Keyword('false')
    k_null = Keyword('null')
    r_name = Regex(r"([\w_][\w0-9\'\^_\!]*)")
    r_num = Regex(r'\d*\.\d*|\d+')
    whatever = Ref()

    r_expression = Ref()
    r_factor = Ref()
    r_term = Ref()
    # r_expression = Prio(
    #    r_factor
        # Sequence(r_factor, Tokens("+ -"), THIS)
    # )
    r_term = Choice(
        Sequence('(', r_expression, ')'),
        Sequence("+", r_term),
        Sequence("-", r_term),
        r_num, r_name, "?"
    )
    r_factor = List(r_term, delimiter=Tokens("* /"), mi=1) 
    #Choice(
    #    Sequence(Repeat(Sequence(r_term, Tokens("/ *")),0), r_term)
    #)
    r_expression = List(r_factor, delimiter=Tokens("+ -"), mi=1)
    # Choice(
    #    Sequence(Repeat(Sequence(r_factor, Tokens("+ -")), 0), r_factor)
    #)

    r_equation = Sequence(r_expression, ks_equa, r_expression)

    # r_constraints = json_list(r_equation)
    # r_list_vars = json_list(r_name)
    # r_vars = json_key("vars", r_list_vars)
    # r_pvars = json_key("pvars", r_list_vars)
    # r_source = json_key("source", r_name)
    # r_target = json_key("target", r_name)
    # r_label = json_key("name",  r_name)

    whatever = Choice(r_string, r_num, r_name,
                      k_true, k_false, k_null,
                      r_equation,
                      json_list(whatever),
                      json_dict(r_name, whatever)
                      )

    r_whatever = json_key(r_name, whatever)
    # r_poly = json_key("constraints", r_constraints)

    # r_transition_key = Choice(r_source, r_target, r_label,
    #                           r_poly, r_whatever)
    # r_transition = json_dict_list(r_transition_key)
    # r_transitions = json_key("transitions", List(r_transition))

    # r_program_key = Choice(r_vars, r_pvars, r_transitions, r_whatever)
    varlist = Sequence("var", List(r_name, delimiter=","), ";")
    statelist = Sequence("states", List(r_name, delimiter=","), ";")
    fr = Sequence("from", ":=", r_name)
    to = Sequence("to", ":=", r_name)
    exp = True
    guard = Sequence("guard", ":=", Choice(r_equation, k_true, k_false))
    cons = List(Choice(k_true, k_false, r_equation), delimiter=",", mi=0)
    action = Sequence("action", ":=", Optional(cons))
    op = Choice(fr,to,guard,action)
    ops = List(op, delimiter=";", opt=True)
    tr = Sequence("transition", r_name, ":=", "{",ops,"}")
    trlist = List(tr, delimiter=";", opt=True)
    strategy = Sequence("strategy", r_name, "{", "Region",r_name, ":=","{","state","=",r_name, "&&", List(r_equation,delimiter="&&", mi=0),"}",";","}")
    model = Sequence("model", r_name, "{",varlist, statelist, trlist,"}")
    START = Sequence(model,strategy) 

    # START = Repeat(r_program, mi=1, ma=1)


class Parser_fst(ParserInterface):

    def parse(self, filepath, debug=False):
        """Parse .fst file

        :param filepath: Full path to file to be parsed.
        :type filepath: str
        :param debug: True to show debug information. Defaults to False
        :type debug: bool
        :returns: :obj:`pyParser.Cfg.Cfg` ControlFlowGraph.
        """
        lines = open(filepath).readlines()

        lines = self.remove_comments(lines)
        return self.parse_string("\n".join(lines))

    def parse_string(self, cad, _=None, debug=False):
        g = FST_Grammar()
        tree = g.parse(cad)
        if not tree.is_valid:
            print(cad)
            raise ValueError(str(cad[tree.pos-15:tree.pos]+"*->*"+cad[tree.pos:tree.pos+15]) + " ("+str(tree.pos)+") -> Expecting: "
                             + str(tree.expecting))
        visitor = FST_Visitor()
        program = visitor.start(tree.tree)
        return self.program2cfg(program)

    def program2cfg(self, program):
        G = Cfg()
        G.add_var_name(program["global_vars"])
        for t in program["transitions"]:
            G.add_edge(**t)
        G.set_init_node(program["initnode"])
        return G

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
        pos = line.find("//")
        if pos >= 0:
            line = line[0:pos]
        pos = line.find("/*")
        if pos >= 0:
            line = line[0:pos]
            multi = True
        return line.replace("\n", ""), multi


class FST_Visitor:

    def start(self, init):
        program = self.v_program(init)
        return program

    def assert_token(self, node, token):
        if node.string == token:
            return True
        else:
            raise ValueError("Expecting token: " + token + " got: "
                             + node.string)

    def assert_list(self, node, mode="list"):
        if len(node.children) != 1:
            raise ValueError("No "+mode+" found.")
        openb = "["
        closeb = "]"
        if mode == "dict":
            openb = "{"
            closeb = "}"
        elem = node.children[0]
        self.assert_token(elem.children[0], openb)
        self.assert_token(elem.children[2], closeb)
        list_elem = elem.children[1].children
        obj = []
        coma = False
        for i in range(0, len(list_elem)):
            if coma:
                self.assert_token(list_elem[i], ",")
            else:
                obj.append(list_elem[i])
            coma = not coma
        return obj

    def find_key(self, key, elems):
        idxs = []
        for i in range(len(elems)):
            if elems[i].children[0].string == key:
                idxs.append(i)
        return idxs

    def v_program(self, node):
        elems = self.assert_list(node, mode="dict")
        program = {}
        var_pos = self.find_key("vars", elems)
        if len(var_pos) != 1:
            raise ValueError("{} variable set definition(s) found."
                             .format(len(var_pos)))
        Vars = self.v_vars(elems[var_pos[0]].children[2])

        pvar_pos = self.find_key("pvars", elems)
        if len(pvar_pos) > 1:
            raise ValueError("{} prime variable set definitions found."
                             .format(len(pvar_pos)))
        elif len(pvar_pos) == 1:
            PVars = self.v_vars(elems[pvar_pos[0]].children[2])
        else:
            PVars = [str(v+"'") for v in Vars]
        if len(Vars) != len(PVars):
            raise ValueError("Different number of variables and"
                             + " prime variables.")
        for pv in PVars:
            if pv in Vars:
                raise ValueError("Prime variable '{}' already".format(pv)
                                 + " defined as variable.")
        self.Global_vars = Vars + PVars
        trans_pos = self.find_key("transitions", elems)
        if len(trans_pos) != 1:
            raise ValueError("{} transition set definition(s) found."
                             .format(len(trans_pos)))

        transitions = self.v_transitions(elems[trans_pos[0]].children[2])
        program["global_vars"] = self.Global_vars
        program["transitions"] = transitions
        initnode_pos = self.find_key("initnode", elems)
        if len(initnode_pos) > 1:
            raise ValueError("{} initnode definitions found."
                             .format(len(initnode_pos)))
        elif len(initnode_pos) == 1:
            program["initnode"] = elems[initnode_pos[0]].children[2].string
        else:
            program["initnode"] = transitions[0]["source"]
        used_pos = var_pos + pvar_pos + trans_pos
        other_pos = [i for i in range(len(elems)) if i not in used_pos]
        for idx in other_pos:
            key, elem = self.v_whatever(elems[idx])
            program[key] = elem
        program["max_local_vars"] = self.max_local_vars
        return program

    def v_whatever(self, node):
        if len(node.children) != 3:
            raise ValueError("unknown")
        self.assert_token(node.children[1], ":")
        key = node.children[0].string
        elem = node.children[2].string
        return key, elem

    def v_vars(self, node):
        ret_vars = []
        l_var = self.assert_list(node, mode="list")
        for c in l_var:
            if c.string in ret_vars:
                raise ValueError("{} already defined.".format(c.string))
            ret_vars.append(str(c.string))
        return ret_vars

    def v_transitions(self, node):
        ret_trans = []
        self.max_local_vars = 0
        l_tr = self.assert_list(node, mode="list")
        for t in l_tr:
            tr = self.v_transition(t)
            if tr is None:
                continue
            ret_trans.append(tr)
        if len(ret_trans) < 1:
            raise ValueError("At least one transition is required.")
        return ret_trans

    def v_transition(self, node):
        l_t = self.assert_list(node, mode="dict")
        self.local_vars = []
        tr = {}
        ign_pos = self.find_key("ignore", l_t)
        if len(ign_pos) > 0:
            return None
        src_pos = self.find_key("source", l_t)
        trg_pos = self.find_key("target", l_t)
        name_pos = self.find_key("name", l_t)
        cons_pos = self.find_key("constraints", l_t)
        if len(src_pos) != 1:
            raise ValueError("{} transition source definition(s) found."
                             .format(len(src_pos)))
        if len(trg_pos) != 1:
            raise ValueError("{} transition target definition(s) found."
                             .format(len(trg_pos)))
        if len(name_pos) != 1:
            raise ValueError("{} transition name definition(s) found."
                             .format(len(name_pos)))
        if len(cons_pos) != 1:
            raise ValueError("{} transition constr set definition(s) found."
                             .format(len(cons_pos)))
        tr["source"] = l_t[src_pos[0]].children[2].string
        tr["target"] = l_t[trg_pos[0]].children[2].string
        tr["name"] = l_t[name_pos[0]].children[2].string

        cons = self.v_constraints(l_t[cons_pos[0]].children[2])
        tr["constraints"] = cons[0]

        dim = len(self.Global_vars)+len(self.local_vars)
        tr_poly = C_Polyhedron(Constraint_System(cons[1]), dim)
        tr["tr_polyhedron"] = tr_poly

        tr["linear"] = cons[2]
        tr["local_vars"] = self.local_vars
        used_pos = src_pos + trg_pos + name_pos + cons_pos
        other_pos = [i for i in range(len(l_t)) if i not in used_pos]
        for idx in other_pos:
            key, elem = self.v_whatever(l_t[idx])
            tr[key] = elem
        if len(self.local_vars) > self.max_local_vars:
            self.max_local_vars = len(self.local_vars)
        self.local_vars = []
        return tr

    def v_constraints(self, node):
        elems = self.assert_list(node, mode="list")
        cons_str = []
        cons = []
        linear = True
        for e in elems:
            con, lin = self.v_constraint(e)
            if not lin:
                linear = False
            cons.append(con)
            cons_str.append(e.string)

        return cons_str, cons, linear

    def v_constraint(self, node):
        con = node.children[0]
        
        e1, l1 = self.v_expression(con.children[0])
        e2, l2 = self.v_expression(con.children[2])

        if not l1 or not l2:
            e1 = Linear_Expression(0)
            e2 = Linear_Expression(0)
            return e1 == e2, False
        comp = con.children[1].string
        if(comp == "<"):
            exp = (e1 <= (e2-1))
        elif(comp == ">"):
            exp = (e1 >= (e2+1))
        elif(comp == "<=" or comp == "=<"):
            exp = (e1 <= e2)
        elif(comp == ">=" or comp == "=>"):
            exp = (e1 >= e2)
        elif(comp == "=" or comp == "=="):
            exp = (e1 == e2)
        else:
            raise ValueError("Expecting compare op getting {}".format(comp))
        if isinstance(exp, bool):
            return (Linear_Expression(0) == Linear_Expression(0)), True
        return exp, True

    def v_expression(self, node):
        num_c = len(node.children)
        if num_c == 0:
            return self.v_term(node), True
        elif num_c == 1:
            return self.v_expression(node.children[0])
        elif num_c == 2:
            if node.children[1].string == "":
                return self.v_term(node.children[0]), True
            exp, linear = self.v_expression(node.children[1])
            if node.children[0].string == "-":
                return -exp, linear
            return exp, linear
        else:
            if node.children[0].string == "(":
                self.assert_token(node.children[2], ")")
                exp, linear = self.v_expression(node.children[1])
                return (exp), linear
            else:
                exp, l1 = self.v_expression(node.children[0])
                for i in range(2, num_c, 2):
                    op = node.children[i-1].string
                    e2, l2 = self.v_expression(node.children[i])
                    if not l1 or not l2:
                        return Linear_Expression(0), False
                    try:
                        if op == "+":
                            exp = exp + e2
                        elif op == "-":
                            exp = exp - e2
                        elif op == "*":
                            exp = exp * e2
                        elif op == "/":
                            exp = exp / e2
                        else:
                            raise ValueError("Expecting operator."
                                             + " Got {}".format(op))
                    except TypeError:
                        return Linear_Expression(0), False
                return exp, l1

    def v_term(self, node):
        val = node.string
        try:
            return int(val)
        except ValueError:
            if val in self.Global_vars:
                return Variable(self.Global_vars.index(val))
            else:
                num_global = len(self.Global_vars)
                if not(val in self.local_vars):
                    self.local_vars.append(val)
                return Variable(num_global + self.local_vars.index(val))

    def iterate(self, node, tab=0):
        cad = ("\t"*tab) + "\"" + str(node.string) + "\""
        if len(node.children) > 0:
            cad += ": {\n"
            for c in node.children:
                cad += self.iterate(c, tab+1) + "\n"
            cad += ("\t"*tab) + "}"
        if tab == 0:
            print(cad)
        return cad


def Main():
    f = Parser_fst()
    import sys
    r = f.parse(sys.argv[1])
    """"r = f.parse_string("{vars : [a,b],pvars : [a',b'],\n transitions:[\n"                 
                       + "{source:n1,target:n1,name:t1,constraints:[(c) <= b, a+b < a*b+b*c],bla:bla},\n"
                       + "{source:n2,target:n2,name:t2,constraints:[a-1-(b-2) > b*2*(4-a), -b+(c*2*a) < c*b*a],bla:bla}\n"
                       + "],a:b}")
    """
    print(r.get_edges())


if __name__ == "__main__":
    Main()
