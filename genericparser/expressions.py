class BoolExpression(object):

    def __init__(self, params):
        raise NotImplementedError()

    def toDNF(self):
        raise NotImplementedError()

    def negate(self):
        raise NotImplementedError()

    def isTrue(self):
        raise NotImplementedError()

    def isFalse(self):
        raise NotImplementedError()


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

    def isTrue(self):
        return self._exp.isFalse()

    def isFalse(self):
        return self._exp.isTrue()


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

    def isTrue(self):
        return (self._left.isFalse() or self._right.isTrue())

    def isFalse(self):
        return (self._left.isTrue() and self._right.isFalse())


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

    def isTrue(self):
        istrue = True
        for e in self._boolexps:
            if not e.isTrue():
                istrue = False
        return istrue

    def isFalse(self):
        for e in self._boolexps:
            if e.isFalse():
                return True
        return False


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

    def isTrue(self):
        for e in self._boolexps:
            if e.isTrue():
                return True
        return False

    def isFalse(self):
        isfalse = True
        for e in self._boolexps:
            if not e.isFalse():
                isfalse = False
        return isfalse

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

    def isFalse(self):
        return False

    def isTrue(self):
        return False


class boolterm(BoolExpression):

    def __init__(self, word):
        if word in ["true", "false"]:
            self._w = word
        else:
            raise ValueError()

    def negate(self):
        if self._w == "true":
            return boolterm("false")
        return boolterm("true")

    def toDNF(self):
        if self._w == "true":
            return inequation("0", "0", ">=").toDNF()
        return inequation("0", "1", ">=").toDNF()

    def __repr__(self):
        return self._w

    def isFalse(self):
        return self._w == "false"

    def isTrue(self):
        return self._w == "true"


class Expression:
    KIND = "expr"


class expterm(Expression):
    KIND = "term"

    def __init__(self, word):
        try:
            self.value = float(word)
            self.elem = "number"
        except ValueError:
            import re
            if re.match("(^([\w_][\w0-9\'\^_\!]*)$)", word):
                self.value = word
                self.elem = "variable"
            else:
                raise ValueError()
