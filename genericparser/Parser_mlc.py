from genericparser.Constraint_parser import ConstraintTreeTransformer
from genericparser import ParserInterface
from genericparser import constants


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

    def parse_string(self, cad, __=None, debug=False):
        from lark.lark import Lark
        parser = Lark(self.get_grammar())
        return self.program2cfg(MlcTreeTransformer().transform(parser.parse(cad)))

    def get_grammar(self):
        return """
        // mlc language
        
        start: _program
        
        _endls: "\n"+
        
        CMP: "<="|"=>"|"=<"|"=="|">="|">"|"<"|"="
        SUM: "+" | "-"
        MUL: "*" | "/" 
        
        CNAME: ("_"|LETTER) ("_"|LETTER|DIGIT|"'"|"^"|"!"|".")*
        name: CNAME
        
        term: [SUM] NUMBER | [SUM] CNAME | "(" expression ")"
        factor: term (MUL term)*
        expression:  factor (SUM factor)*
        
        constraint: expression CMP expression
        
        transition: "!path" _endls (constraint _endls)+
        
        transitions: (transition)+
        
        vars: (name)+
        pvars: (name)+

        _program: _endls? "!vars" _endls vars _endls ("!pvars" _endls pvars _endls)? transitions

        COMMENT: /\/\*([^*]*|([^*]*\*+[^*\/]+)*)\*+\//
        | "//" /[^\n]*/
        | /#[^\n]*/

        %import common.NUMBER
        %import common.LETTER
        %import common.WORD
        %import common.DIGIT
        %ignore " "
        %ignore "\t"
        %ignore "\r"
        %ignore COMMENT
        """


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
                raise ValueError("Different number of variables and" +
                                 " prime variables.")
        else:
            pvars = [v + "'" for v in g_vars]

        program[constants.variables] = g_vars + pvars
        for i in range(len(program[constants.variables]) - 1):
            if program[constants.variables][i] in program[constants.variables][i + 1:]:
                raise ValueError("Multiple definition of variable: {}".format(program[constants.variables][i]))

        program["transitions"] = node[-1]

        set_gvars = set(program[constants.variables])
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
            tr[constants.transition.constraints] = t
            for c in t:
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
        program[constants.initnode] = program["transitions"][0]["source"]
        program["max_local_vars"] = max_local_vars
        return program
