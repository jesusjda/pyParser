from genericparser.Constraint_parser import ConstraintTreeTransformer
from genericparser import ParserInterface
from lpi import Expression
from genericparser import constants


class Parser_kittle(ParserInterface):

    def parse(self, filepath, debug=False):
        """Parse .kittle file

        :param filepath: Full path to file to be parsed.
        :type filepath: str
        :param debug: True to show debug information. Defaults to False
        :type debug: bool
        :returns: :obj:`pyParser.Cfg.Cfg` ControlFlowGraph.
        """
        with open(filepath) as file:
            text = file.read()
        return self.parse_string(text, debug=debug)

    def parse_string(self, cad, __=None, debug=False):
        from lark.lark import Lark
        parser = Lark(self.get_grammar())
        return self.program2cfg(KittleTreeTransformer().transform(parser.parse(cad)))

    def get_grammar(self):
        return """
        // koat
        start: _program
        
        CMP: "<="|"=>"|"=<"|"=="|">="|">"|"<"|"="
        SUM: "+" | "-"
        MUL: "*" | "/" 
        
        CNAME: ("_"|LETTER) ("_"|LETTER|DIGIT|"'"|"^"|"!"|".")*
        
        term: [SUM] NUMBER | [SUM] CNAME | "(" expression ")"
        factor: term (MUL term)*
        expression:  factor (SUM factor)*
        
        constraint: expression CMP expression
        
        name: CNAME
        number: NUMBER
        
        _goal: "(" "GOAL" name ")"
        _startterm: "(" "STARTTERM" entry ")"
        
        entry: name -> noentry
        | "(" "FUNCTIONSYMBOLS" name ")"
        
        variables: "(" "VAR" name* ")"
        
        node: name "(" (expression ("," expression)*)? ")"
        _and: "&&" | "/\\\\"
        constraints: ("[" constraint ( _and constraint)* "]")
        | (":|:" constraint ( _and constraint)*)
        
        _right_hand: node
        | ("Com_1" "(" node ")")
        
        
        rule: node "->" _right_hand constraints?
        
        rules: "(" "RULES" rule* ")" 
        
        _program: rule+
        
        COMMENT: /\\/\\*([^*]*|([^*]*\\*+[^*\\/]+)*)\\*+\\//
        | "//" /[^\\n]*/
        | /#[^\\n]*/
        
        %import common.ESCAPED_STRING
        %import common.SIGNED_NUMBER
        %import common.NUMBER
        %import common.LETTER
        %import common.WORD
        %import common.DIGIT
        %import common.WS
        %ignore WS
        %ignore COMMENT
        """

class KittleTreeTransformer(ConstraintTreeTransformer):
    name = lambda self, node: str(node[0])
    entry = lambda self, node: node[0]
    constraints = list
    rules = variables = list
    rule = node = list

    def start(self, node):
        program = {}
        N = 0
        g_vars = []
        for idx in range(len(node)):
            if len(node[idx][0]) > N:
                N = len(node[idx][0])
                g_vars = node[idx][0][1:]
        entry = node[0][0][0]
        g_vars = [str(v) for v in g_vars]
        N -= 1
        transitions = node
        program[constants.variables] = g_vars + [v + "'" for v in g_vars]
        g_vars = program[constants.variables]
        for i in range(len(program[constants.variables]) - 1):
            if program[constants.variables][i] in program[constants.variables][i + 1:]:
                raise ValueError("Multiple definition of variable: {}".format(program[constants.variables][i]))

        set_gvars = set(program[constants.variables])
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
            tr["name"] = "t" + str(count)
            count += 1
            # add init constraints
            for idx in range(len(left)):
                if str(left[idx]) == g_vars[idx]:
                    continue
                cons.append(left[idx] == Expression(g_vars[idx]))
            # add post constraints
            for idx in range(len(right)):
                cons.append(right[idx] == Expression(g_vars[N + idx]))
            tr[constants.transition.constraints] = cons
            linear = True
            l_vars = []
            for c in tr[constants.transition.constraints]:
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
        program["transitions"] = trs
        program[constants.initnode] = entry
        program["max_local_vars"] = max_local_vars
        return program
