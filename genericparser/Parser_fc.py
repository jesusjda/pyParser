from genericparser.Constraint_parser import ConstraintTreeTransformer
from genericparser import ParserInterface
from lpi import Constraint
from genericparser import constants


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

    def parse_string(self, cad, __=None, debug=False):
        from lark.lark import Lark
        parser = Lark(self.get_grammar(), parser='lalr')
        return self.program2cfg(FcTreeTransformer().transform(parser.parse(cad)))

    def get_grammar(self):
        return """
        // fc language based on json
        start:dict
        CMP: "<="|"=>"|"=<"|"=="|">="|">"|"<"|"="
        SUM: "+" | "-"
        MUL: "*" | "/" 
        
        CNAME: ("_"|LETTER) ("_"|LETTER|DIGIT|"'"|"^"|"!"|".")*
        
        term: [SUM] NUMBER | [SUM] CNAME | "(" expression ")"
        factor: term (MUL term)*
        expression:  factor (SUM factor)*
        
        constraint: expression CMP expression
        name: CNAME
        string: ESCAPED_STRING
        bool: "true" | "false"
        null: "null"
        _value: dict
        | list
        | string
        | expression
        | constraint
        | bool
        | null
        
        
        key: CNAME | NUMBER | ESCAPED_STRING
        !namekey : "source" | "target"  | "name"  | "initnode" | "domain"
        !lvarskey : "vars" | "pvars"
        
        list : "[" [_value ("," _value)* ","?]  "]"
        lvars : "[" [name ("," name)* ","?] "]"
        dict : "{" [pair ("," pair)* ","?] "}"
        pair : key ":" _value
        | namekey ":" name
        | lvarskey ":" lvars
        
        
        COMMENT: /\/\*([^*]*|([^*]*\*+[^*\/]+)*)\*+\//
        | "//" /[^\n]*/
        | /#[^\n]*/
        
        %import common.ESCAPED_STRING
        %import common.NUMBER
        %import common.LETTER
        %import common.WORD
        %import common.DIGIT
        %import common.WS
        %ignore WS
        %ignore COMMENT
        """

class FcTreeTransformer(ConstraintTreeTransformer):

    list = list
    lvars = list
    pair = tuple
    null = lambda self, __: None
    true = lambda self, __: True
    false = lambda self, __: False
    key = lambda self, node: str(node[0])
    namekey = lambda self, node: str(node[0])
    lvarskey = lambda self, node: str(node[0])
    name = lambda self, node: str(node[0])

    def dict(self, node):
        keys = []
        for n in node:
            k, __ = n
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
        program[constants.variables] = program["vars"]

        if _check_key(program, "pvars", optional=True):
            if len(program["vars"]) != len(program["pvars"]):
                raise ValueError("Different number of variables and" +
                                 " prime variables.")
            program[constants.variables] += program["pvars"]
            program.pop("pvars", None)
        else:
            program[constants.variables] += [v + "'" for v in program["vars"]]
        program.pop("vars", None)

        for i in range(len(program[constants.variables]) - 1):
            if program[constants.variables][i] in program[constants.variables][i + 1:]:
                raise ValueError("Multiple definition of variable: {}".format(program[constants.variables][i]))

        _check_key(program, "transitions")
        program["transitions"] = [tr for tr in program["transitions"] if not _check_key(tr, "ignore", optional=True)]
        set_gvars = set(program[constants.variables])
        max_local_vars = 0
        trs = []
        trs_name = [t["name"] for t in program["transitions"] if "name" in t]
        rnd_name_count = 0
        it_trs = 0
        for tr in program["transitions"]:
            _check_key(tr, "source")
            _check_key(tr, "target")
            if not _check_key(tr, "name", optional=True):
                from termination.output import Output_Manager as OM
                tr_name = "tr" + str(rnd_name_count)
                while tr_name in trs_name:
                    rnd_name_count += 1
                    tr_name = "tr" + str(rnd_name_count)
                rnd_name_count += 1
                tr["name"] = tr_name
                OM.printif(2, "WARNING: no transition name for a transition" +
                           " from {} to {}. Name given: {}".format(tr["source"], tr["target"], tr["name"]))
                trs_name.append(tr_name)
            else:
                it_trs += 1
                if tr["name"] in trs_name[it_trs:]:
                    raise ValueError("Multiple transitions with the same name: {}.".format(tr["name"]))
            _check_key(tr, constants.transition.constraints)
            linear = True
            l_vars = []
            for c in tr[constants.transition.constraints]:
                if not isinstance(c, Constraint):
                    raise ValueError("No-constraint object ({}) found at transition {}.".format(c, tr["name"]))
                if not c.is_linear():
                    linear = False
                ll_vars = [x for x in c.get_variables()
                           if x not in set_gvars]
                l_vars.extend(x for x in ll_vars
                              if x not in l_vars)
            if len(l_vars) > max_local_vars:
                max_local_vars = len(l_vars)
            tr[constants.transition.islinear] = linear
            tr[constants.transition.localvariables] = l_vars
            trs.append(tr)
        program.update(transitions=trs)
        if _check_key(program, "initnode", optional=True):
            program[constants.initnode] = program["initnode"]
            program.pop("initnode", None)
        elif not _check_key(program, constants.initnode, optional=True):
            program[constants.initnode] = program["transitions"][0]["source"]
        program["max_local_vars"] = max_local_vars
        return program
