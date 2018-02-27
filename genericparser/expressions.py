class Expression(object):
    
    def __init__(self, arg1, op=None, arg2=None):
        if not isinstance(arg1, Expression):
            raise ValueError()
        self._left = arg1
        self._op = op
        self._right = arg2
        if arg2:
            if(not op or
               not(op in ["+","-","/","*"]) or
               not isinstance(arg2, Expression)):
                raise ValueError()
        elif op and op != "-":
            raise ValueError()
        else:
            self._right = arg1
            self._op = "-"
            self._left = expterm(0)
        rd = self._right.degree()
        ld = self._left.degree()
        if op in ["*", "/"]:
            self._degree = ld + rd
        else:
            self._degree = max(ld, rd)

    def degree(self):
        return self._degree
    
    def is_linear(self):
        return self._degree < 2

    def get(self, variables, number):
        """
        variables: dictionary which keys are the variables name.
        number: class of numbers (e.g for ppl use Linear_Expression, for z3 use Real
        """
        exp = self._left.get(variables, number)
        e2 = self._right.get(variables, number)
        if self._op == "-":
            exp = exp - e2
        elif self._op == "+":
            exp = exp + e2
        elif self._op == "*":
            exp = exp * e2
        elif self._op == "/":
            exp = exp / e2
        return exp

    def transform(self, variables, lib="ppl"):
        """
        variables: list of variables (including prime and local variables)
        lib: "z3" or "ppl"
        """
        if lib == "ppl":
            from ppl import Linear_Expression
            from ppl import Variable
            match = {}
            count = 0
            for v in variables:
                match[v] = Variable(count)
                count += 1
            return self.get(match, Linear_Expression)
        elif lib == "z3":
            from z3 import Real
            match = {v:Real(v) for v in variables}
            return self.get(match, Real)
        else:
            raise ValueError("lib ({}) not supported".format(lib))

    def __add__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = expterm(other)
        elif not isinstance(other, (expterm, Expression)):
            raise NotImplementedError()
        return Expression(self, "+", right)

    def __sub__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = expterm(other)
        elif not isinstance(other, (expterm, Expression)):
            raise NotImplementedError()
        return Expression(self, "-", right)

    def __mul__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = expterm(other)
        elif not isinstance(other, (expterm, Expression)):
            raise NotImplementedError()
        return Expression(self, "*", right)

    def __truediv__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = expterm(other)
        elif not isinstance(other, (expterm, Expression)):
            raise NotImplementedError()
        return Expression(self, "/", right)

    def __neg__(self):
        return self*(-1)

    def __pos__(self):
        return self

    def __radd__(self, other):
        left = other
        if isinstance(other, (float, int)):
            left = expterm(other)
        elif not isinstance(other, (expterm, Expression)):
            raise NotImplementedError()
        return Expression(left, "+", self)

    def __rsub__(self, other):
        left = other
        if isinstance(other, (float, int)):
            left = expterm(other)
        elif not isinstance(other, (expterm, Expression)):
            raise NotImplementedError()
        return Expression(left, "-", self)

    def __rmul__(self, other):
        left = other
        if isinstance(other, (float, int)):
            left = expterm(other)
        elif not isinstance(other, (expterm, Expression)):
            raise NotImplementedError()
        return Expression(left, "*", self)

    def __rtruediv__(self, other):
        left = other
        if isinstance(other, (float, int)):
            left = expterm(other)
        elif not isinstance(other, (expterm, Expression)):
            raise NotImplementedError()
        return Expression(left, "/", self)

    def __lt__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = expterm(other)
        elif not isinstance(other, (expterm, Expression)):
            raise NotImplementedError()
        return inequation(self, "<", right)

    def __le__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = expterm(other)
        elif not isinstance(other, (expterm, Expression)):
            raise NotImplementedError()
        return inequation(self, "<=", right)

    def __eq__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = expterm(other)
        elif not isinstance(other, (expterm, Expression)):
            raise NotImplementedError()
        return inequation(self, "==", right)

    def __gt__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = expterm(other)
        elif not isinstance(other, (expterm, Expression)):
            raise NotImplementedError()
        return inequation(self, ">", right)

    def __ge__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = expterm(other)
        elif not isinstance(other, (expterm, Expression)):
            raise NotImplementedError()
        return inequation(self, ">=", right)

    def toString(self, variables=None):
        aux = self._left.toString(variables)
        if self._op:
            aux += " {} {}".format(self._op, self._right.toString(variables))
        return "({})".format(aux)

    def __repr__(self):
        return self.toString()

class expterm(Expression):

    def __init__(self, word):
        if isinstance(word, (float, int)):
            self.value = word
            self.elem = "number"
        else:
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

    def degree(self):
        if self.elem == "number":
            return 0
        else:
            return 1

    def get(self, variables, number):
        if self.elem == "number":
            try:
                return number(self.value)
            except Exception:
                return number(str(self.value))
        else:
            return variables[self.value]

    def __neg__(self):
        if self.elem == "number":
            return expterm(-self.value)
        else:
            return self*(-1)

    def toString(self, variables=None):
        if self.elem == "number":
            return str(self.value)
        else:
            if variables:
                return "{}".format(variables[self.value])
            else:
                return str(self.value)


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


class inequation(BoolExpression, Expression):

    def __init__(self, left, op, right):
        if(not isinstance(left, Expression) or
           not isinstance(right, Expression) or
           not(op in ["<", "<=", "=<", "=", "==", "=>", ">=", ">"])):
            raise ValueError()
        self._left = left
        self._op = op
        self._right = right
        rd = self._right.degree()
        ld = self._left.degree()
        self._degree = max(ld, rd)

    def negate(self):
        if self._op in ["=", "=="]:
            return Or(inequation(self._left, "<", self._right),
                      inequation(self._left, ">", self._right))
        elif self._op == ">":
            op = "<="
        elif self._op in [">=", "=>"]:
            op = "<"
        elif self._op == "<":
            op = ">="
        elif self._op in ["<=", "=<"]:
            op = ">"
        return inequation(self._left, op, self._right)

    def toString(self, variables=None):
        return "{} {} {}".format(self._left.toString(variables),
                                 str(self._op),
                                 self._right.toString(variables))

    def toDNF(self):
        return [[self]]

    def isFalse(self):
        return False

    def isTrue(self):
        return False

    def get(self, variables, number):
        left = self._left.get(variables, number)
        right = self._right.get(variables, number)
        if self._op in ["=", "=="]:
            return (left == right)
        elif self._op == ">":
            return (left >= right + number(1))
        elif self._op in [">=", "=>"]:
            return (left >= right)
        elif self._op == "<":
            return (left <= right -  number(1))
        elif self._op in ["<=", "=<"]:
            return (left <= right)


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
            return inequation("0", ">=", "0").toDNF()
        return inequation("0", ">=", "1").toDNF()

    def __repr__(self):
        return self._w

    def isFalse(self):
        return self._w == "false"

    def isTrue(self):
        return self._w == "true"
