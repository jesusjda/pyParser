from genericparser.Constraint_parser import ConstraintTreeTransformer
from genericparser import ParserInterface
from .expressions import expterm

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
        return self.parse_string(fctext,debug=debug)
    
    def parse_string(self, cad, _=None, debug=False):
        import os
        grammarfile = os.path.join(os.path.dirname(__file__),"koat.g")
        with open(grammarfile, "r") as grammar:
            g = grammar.read()
        from lark.lark import Lark
        l = Lark(g)
        return self.program2cfg(KoatTreeTransformer().transform(l.parse(cad)))


class KoatTreeTransformer(ConstraintTreeTransformer):
    
    name = lambda self, node: str(node[0])
    entry = lambda self, node: node[0]
    constraints = list
    rules = variables = list
    rule = node = list

    def start(self, node):
        program = {}
        program["goal"] = node[0]
        entry = node[1]
        g_vars = node[2]
        N = len(g_vars)
        transitions = node[3]
        program["global_vars"] = g_vars + [v+"'" for v in g_vars]
        g_vars = program["global_vars"]
        for i in range(len(program["global_vars"])-1):
            if program["global_vars"][i] in program["global_vars"][i+1:]:
                raise ValueError("Multiple definition of variable: {}".format(program["global_vars"][i]))

        set_gvars = set(program["global_vars"])
        max_local_vars = 0
        trs = []
        count = 0
        for t in transitions:
            tr = {}
            if len(t) == 3:
                left, right, cons = t
            else:
                left, right = t
                cons = []
            tr["source"] = left.pop(0)
            tr["target"] = right.pop(0)
            tr["name"] = "t"+str(count)
            count+=1
            # add init constraints
            for idx in range(len(left)):
                if str(left[idx]) == g_vars[idx]:
                    continue
                cons.append(left[idx] == expterm(g_vars[idx]))
            # add post constraints
            for idx in range(len(right)):
                cons.append(right[idx] == expterm(g_vars[N+idx]))
            tr["constraints"] = cons
            linear = True
            l_vars = []
            for c in tr["constraints"]:
                if not c.is_linear():
                    linear = False
                ll_vars = [x for x in c.get_variables()
                           if x not in set_gvars]
                l_vars.extend(x for x in ll_vars
                              if x not in l_vars)
            if len(l_vars) > max_local_vars:
                max_local_vars = len(l_vars)
            tr["linear"] = linear
            tr["local_vars"] = l_vars
            trs.append(tr)
        program["transitions"] =trs
        if entry:
            program["init_node"] = entry
        else:
            program["init_node"] = program["transitions"][0]["source"]
        program["max_local_vars"] = max_local_vars
        return program
