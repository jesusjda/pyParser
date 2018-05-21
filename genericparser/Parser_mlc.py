from genericparser.Constraint_parser import ConstraintTreeTransformer
from genericparser import ParserInterface


class Parser_mlc(ParserInterface):
    
    def parse(self, filepath, debug=False):
        """Parse .mlc file

        :param filepath: Full path to file to be parsed.
        :type filepath: str
        :param debug: True to show debug information. Defaults to False
        :type debug: bool
        :returns: :obj:`pyParser.Cfg.Cfg` ControlFlowGraph.
        """
        with open(filepath) as file:
            fctext = file.read()
        return self.parse_string(fctext, debug=debug)
    
    def parse_string(self, cad, _=None, debug=False):
        import os
        grammarfile = os.path.join(os.path.dirname(__file__), "mlc.g")
        with open(grammarfile, "r") as grammar:
            g = grammar.read()
        from lark.lark import Lark
        l = Lark(g)
        return self.program2cfg(MlcTreeTransformer().transform(l.parse(cad)))


class MlcTreeTransformer(ConstraintTreeTransformer):
    
    name = lambda self, node: str(node[0])
    transition = list
    transitions = list
    vars = pvars = list

    def start(self, node):
        program = {}
        
        g_vars = node[0]
        if len(node) == 3:
            pvars = node[1]
            if len(g_vars) != len(pvars):
                raise ValueError("Different number of variables and"
                                 + " prime variables.")
        else:
            pvars = [v + "'" for v in g_vars]

        program["global_vars"] = g_vars + pvars
        for i in range(len(program["global_vars"]) - 1):
            if program["global_vars"][i] in program["global_vars"][i + 1:]:
                raise ValueError("Multiple definition of variable: {}".format(program["global_vars"][i]))

        program["transitions"] = node[-1]

        set_gvars = set(program["global_vars"])
        max_local_vars = 0
        trs = []
        count = 0
        for t in program["transitions"]:
            tr = {}
            tr["source"] = tr["target"] = "n"
            tr["name"] = "t" + str(count)
            count += 1
            linear = True
            l_vars = []
            tr["constraints"] = t
            for c in t:
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
        program.update(transitions=trs)
        program["init_node"] = program["transitions"][0]["source"]
        program["max_local_vars"] = max_local_vars
        print(program)
        return program
