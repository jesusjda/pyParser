from .expressions import expterm
from .expressions import Expression
from lark import Transformer


class ConstraintTreeTransformer(Transformer):
    """To use this parser, you must add ConstraintTreeTransformer
    as parent of your transformer. Also, your syntax should
    include:

    CMP: "<="|"=>"|"=<"|"=="|">="|">"|"<"|"="
    SUM: "+" | "-"
    MUL: "*" | "/"

    CNAME: ("_"|LETTER) ("_"|LETTER|DIGIT|"'"|"^"|"!")*

    term: [SUM] NUMBER | [SUM] CNAME | "(" expression ")"
    factor: term (MUL term)*
    expression:  factor (SUM factor)*

    constraint: expression CMP expression
    """

    def constraint(self, node):
        e1 = node[0]
        e2 = node[2]

        comp = node[1]
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
        return exp

    def expression(self, node):
        exp = node[0]
        for i in range(2, len(node), 2):
            op = node[i-1]
            e2 = node[i]
            if op == "+":
                exp = exp + e2
            elif op == "-":
                exp = exp - e2
        return exp

    def factor(self, node):
        exp = node[0]
        for i in range(2, len(node), 2):
            op = node[i-1]
            e2 = node[i]
            if op == "*":
                exp = exp * e2
            elif op == "/":
                exp = exp / e2
        return exp

    def term(self, node):
        if isinstance(node[0], Expression):
            return node[0]
        elif len(node) == 2:
            val = node[1]
        else:
            val = node[0]
        try:
            float(val)
        except ValueError:
            pass
        finally:
            if node[0]=="-":
                return expterm(0) - expterm(val)
            else:
                return expterm(val)
