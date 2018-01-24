from . import BoolExpression


class Not(BoolExpression):

    def __init__(self, exp):
        if isinstance(exp, BoolExpression):
            self._exp = exp
        else:
            raise ValueError()

    def negate(self):
        return self._exp

    def toDNF(self):
        neg_exp = self._exp.negate()
        return neg_exp.toDNF()

    def __repr__(self):
        return "¬(" + str(self._exp) + ")"


class Implies(BoolExpression):

    def __init__(self, left, right):
        if(not isinstance(left, BoolExpression)
           or not isinstance(right, BoolExpression)):
            raise ValueError()
        self._left = left
        self._right = right

    def negate(self):
        return And(self._left, self._right.negate())

    def toDNF(self):
        dnf_left = self._left.negate().toDNF()
        dnf_right = self._right.toDNF()
        return dnf_left+dnf_right

    def __repr__(self):
        return str(self._left)+"->"+str(self._right)


class And(BoolExpression):

    def __init__(self, *params):
        for e in params:
            if not isinstance(e, BoolExpression):
                raise ValueError()
        self._boolexps = params

    def negate(self):
        exps = []
        for e in self._boolexps:
            exps.append(e.negate())
        return Or(*exps)

    def toDNF(self):
        dnfs = [e.toDNF() for e in self._boolexps]
        head = [[]]
        for dnf in dnfs:
            new_head = []
            for exp in dnf:
                new_head += [c+exp for c in head]
            head = new_head
        return head

    def __repr__(self):
        s = [str(e) for e in self._boolexps]
        return "(" + " ^ ".join(s) + ")"


class Or(BoolExpression):

    def __init__(self, *params):
        for e in params:
            if not isinstance(e, BoolExpression):
                raise ValueError()
        self._boolexps = params

    def negate(self):
        exps = []
        for e in self._boolexps:
            exps.append(e.negate())
        return And(*exps)

    def toDNF(self):
        dnfs = [e.toDNF() for e in self._boolexps]
        head = []
        for dnf in dnfs:
            head += dnf
        return head

    def __repr__(self):
        s = [str(e) for e in self._boolexps]
        return "(" + " v ".join(s) + ")"


class inequation(BoolExpression):

    def __init__(self, left, right, operator):
        self._left = left
        self._right = right
        self._op = operator

    def negate(self):
        if self._op in ["=", "=="]:
            return Or(inequation(self._left, self._right, "<"),
                      inequation(self._left, self._right, ">"))
        elif self._op == ">":
            op = "<="
        elif self._op in [">=", "=>"]:
            op = "<"
        elif self._op == "<":
            op = ">="
        elif self._op in ["<=", "=<"]:
            op = ">"
        return inequation(self._left, self._right, op)

    def __repr__(self):
        return str(self._left) + str(self._op) + str(self._right)

    def toDNF(self):
        return [[self]]
