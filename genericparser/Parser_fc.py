from genericparser.Constraint_parser import ConstraintTreeTransformer
from . import ParserInterface
from genericparser.expressions import inequality


class Parser_fc(ParserInterface):
    
    def parse(self, filepath, debug=False):
        """Parse .fc file

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
        grammarfile = os.path.join(os.path.dirname(__file__), "fc.g")
        with open(grammarfile, "r") as grammar:
            g = grammar.read()
        from lark.lark import Lark
        l = Lark(g, parser='lalr')
        return self.program2cfg(FcTreeTransformer().transform(l.parse(cad)))


class FcTreeTransformer(ConstraintTreeTransformer):
    
    list = list
    lvars = list
    pair = tuple
    null = lambda self, _: None
    true = lambda self, _: True
    false = lambda self, _: False
    key = lambda self, node: str(node[0])
    namekey = lambda self, node: str(node[0])
    lvarskey = lambda self, node: str(node[0])
    name = lambda self, node: str(node[0])

    def dict(self, node):
        keys = []
        for n in node:
            k, _ = n
            if k in keys:
                raise ValueError("Duplicate key: {}".format(k))
            keys.append(k)
        return dict(node)

    def start(self, node):

        def _check_key(dic, key, optional=False):
            isin = key in dic
            if not isin and not optional:
                raise ValueError("{} key not found.".format(key))
            return isin

        program = node[0]
        _check_key(program, "vars")
        program["global_vars"] = program["vars"]

        if _check_key(program, "pvars", optional=True):
            if len(program["vars"]) != len(program["pvars"]):
                raise ValueError("Different number of variables and"
                                 + " prime variables.")
            program["global_vars"] += program["pvars"]
            program.pop("pvars", None)
        else:
            program["global_vars"] += [v + "'" for v in program["vars"]]
        program.pop("vars", None)

        for i in range(len(program["global_vars"]) - 1):
            if program["global_vars"][i] in program["global_vars"][i + 1:]:
                raise ValueError("Multiple definition of variable: {}".format(program["global_vars"][i]))

        _check_key(program, "transitions")
        program["transitions"] = [tr for tr in program["transitions"] if not _check_key(tr, "ignore", optional=True)]
        set_gvars = set(program["global_vars"])
        max_local_vars = 0
        trs = []
        trs_name = [t["name"] for t in program["transitions"] if "name" in t]
        rnd_name_count = 0
        it_trs=0
        for tr in program["transitions"]:
            _check_key(tr, "source")
            _check_key(tr, "target")
            if not _check_key(tr, "name", optional=True):
                from termination.output import Output_Manager as OM
                tr_name = "tr"+str(rnd_name_count)
                while tr_name in trs_name:
                    rnd_name_count += 1
                    tr_name = "tr"+str(rnd_name_count)
                rnd_name_count += 1
                tr["name"] = tr_name
                OM.printif(2, "WARNING: no transition name for a transition from {} to {}. Name given: {}".format(tr["source"],tr["target"],tr["name"]))
                trs_name.append(tr_name)
            else:
                it_trs += 1
                if tr["name"] in trs_name[it_trs:]:
                    raise ValueError("Multiple transitions with the same name: {}.".format(tr["name"]))
            _check_key(tr, "constraints")
            linear = True
            l_vars = []
            for c in tr["constraints"]:
                if not isinstance(c, inequality):
                    raise ValueError("No-constraint object ({}) found at transition {}.".format(c, tr["name"]))
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
        if _check_key(program, "initnode", optional=True):
            program["init_node"] = program["initnode"]
            program.pop("initnode", None)
        elif not _check_key(program, "init_node", optional=True):
            program["init_node"] = program["transitions"][0]["source"]
        program["max_local_vars"] = max_local_vars
        return program
