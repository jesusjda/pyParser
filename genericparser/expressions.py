class Expression(object):
    
    def __init__(self, left, op, right):
        if not isinstance(left, Expression):
            try:
                left = ExprTerm(left)
            except ValueError:
                raise ValueError("left argument is not a valid Expression.")
        if not isinstance(right, Expression):
            try:
                right = ExprTerm(right)
            except ValueError:
                raise ValueError("right argument is not a valid Expression.")
        if not op in "+-*/":
            raise ValueError("{} is not a valid Operation.".format(op))
        from collections import Counter
        summands = []
        if op == "/":
            if(len(right._summands) > 1 or
               len(right._summands[0][1]) > 0):
                raise TypeError("Unsupported division by polynom.")
            else:
                r_coeff = right._summands[0][0]
                if r_coeff == 0:
                    raise TypeError("Division by zero.")
                for s in left._summands:
                    coeff = s[0] / r_coeff
                    if coeff != 0:
                        summands.append((coeff, s[1]))
        elif op == "*":
            tmp_summands = []
            for l_s in left._summands:
                l_coeff, l_vars = l_s
                for l_r in right._summands:
                    coeff = l_coeff * l_r[0]
                    var = l_vars + l_r[1]
                    var.sort()
                    if coeff != 0:
                        tmp_summands.append((coeff, var))
            while len(tmp_summands) > 0:
                coeff, vs = tmp_summands[0]
                tmp_summands.remove(tmp_summands[0])
                for sr in tmp_summands:
                    if Counter(vs) == Counter(sr[1]):
                        coeff += sr[0]
                        tmp_summands.remove(sr)
                if coeff != 0:
                    summands.append((coeff, vs))
        elif op in ["+", "-"]:
            symb = 1
            if op == "-":
                symb = -1
            pending_summands = right._summands
            for s in left._summands:
                coeff, vs = s
                for sr in pending_summands:
                    if Counter(vs) == Counter(sr[1]):
                        coeff += symb * sr[0]
                        pending_summands.remove(sr)
                if coeff != 0:
                    summands.append((coeff, vs))
            for coeff, vs in pending_summands:
                if coeff != 0:
                    summands.append((symb * coeff, vs))
        self._summands = summands
        self._update()

    def _update(self):
        mx_degree = 0
        var_set = set()
        for s in self._summands:
            if s[0] == 0:
                self._summands.remove(s)
                continue
            var_set = var_set.union(s[1])
            if len(s[1]) > mx_degree:
                mx_degree = len(s[1])
        self._vars = list(var_set)
        del var_set
        self._degree = mx_degree

    def degree(self):
        return self._degree
    
    def is_linear(self):
        return self._degree < 2

    def get_variables(self):
        return self._vars
    
    def get_coeff(self, variables=[]):
        if isinstance(variables, str):
            variables = [variables]
        from collections import Counter
        for sr in self._summands:
            if Counter(variables) == Counter(sr[1]):
                return sr[0]
        return 0
    
    def toString(self, toVar, number):
        txt = ""
        for s in self._summands:
            txt_s = ""
            if len(s[1]) > 0:
                if number(s[0]) != number(1) and number(s[0]) != number(-1):
                    txt_s += str(number(s[0])) + " * "
                elif number(s[0]) == number(-1):
                    txt_s += "- "
                txt_s += " * ".join([toVar(v) for v in s[1]])
            elif number(s[0]) != number(0.0):
                txt_s = str(number(s[0]))

            if number(s[0]) > number(0.0) and txt != "":
                txt += " + "
            elif txt != "":
                txt += " "
            txt += txt_s
        if txt == "":
            txt = "0"
        return txt

    def __repr__(self):
        return self.toString(str, int)
    
    def get(self, toVar, toNum, toExp):
        """
        variables: dictionary which keys are the variables name.
        number: class of numbers (e.g for ppl use Linear_Expression, for z3 use Real
        """
        exp = toExp(0)
        for s in self._summands:
            s_exp = toNum(s[0])
            for v in s[1]:
                s_exp *= toVar(v)
            exp += s_exp
        return exp
    
    def transform(self, variables, lib="ppl"):
        """
        variables: list of variables (including prime and local variables)
        lib: "z3" or "ppl"
        """
        if lib == "ppl":
            from ppl import Linear_Expression
            from ppl import Variable

            def toVar(v):
                if v in variables:
                    return Variable(variables.index(v))
                else:
                    raise ValueError("{} is not a variable.".format(v))

            return self.get(toVar, int, Linear_Expression)
        elif lib == "z3":

            def nope(v):
                return v

            from z3 import Real

            def toVar(v):
                if v in variables:
                    return Real(v)
                else:
                    raise ValueError("{} is not a variable.".format(v))

            return self.get(toVar, Real, nope)
        else:
            raise ValueError("lib ({}) not supported".format(lib))

    def __add__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(self, "+", right)

    def __sub__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(self, "-", right)

    def __mul__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(self, "*", right)

    def __truediv__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(self, "/", right)

    def __neg__(self):
        return self * (-1)

    def __pos__(self):
        return self

    def __radd__(self, other):
        left = other
        if isinstance(other, (float, int)):
            left = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(left, "+", self)

    def __rsub__(self, other):
        left = other
        if isinstance(other, (float, int)):
            left = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(left, "-", self)

    def __rmul__(self, other):
        left = other
        if isinstance(other, (float, int)):
            left = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(left, "*", self)

    def __rtruediv__(self, other):
        left = other
        if isinstance(other, (float, int)):
            left = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(left, "/", self)

    def __lt__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return inequality(self, "<", right)

    def __le__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return inequality(self, "<=", right)

    def __eq__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return inequality(self, "==", right)

    def __gt__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return inequality(self, ">", right)

    def __ge__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return inequality(self, ">=", right)


class ExprTerm(Expression):
    
    def __init__(self, value):
        vs = []
        coeff = 1
        if isinstance(value, (float, int)):
            coeff = value
        else:
            try:
                coeff = float(value)
            except ValueError:
                import re
                vlist = value
                if not isinstance(value, list):
                    vlist = [value]
                vs = []
                for v in vlist:
                    if re.match("(^([\w_][\w0-9\'\^_\!\.]*)$)", v):
                        vs.append(v)
                    else:
                        raise ValueError("{} is not a valid Term.".format(v))
        self._summands = [(coeff, vs)]
        self._update()

    def __neg__(self):
        if self.elem == "number":
            return ExprTerm(-self.value)
        else:
            return self * (-1)


class Expressiona(object):
    
    def __init__(self, arg1, op=None, arg2=None):
        if not isinstance(arg1, Expression):
            raise ValueError()
        self._left = arg1
        self._op = op
        self._right = arg2
        
        if arg2:
            if(not op or
               not(op in ["+", "-", "/", "*"]) or
               not isinstance(arg2, Expression)):
                raise ValueError()
        elif op and op != "-":
            raise ValueError()
        else:
            self._right = arg1
            self._op = "-"
            self._left = ExprTerm(0)
        # calculate variables
        self._vars = self._left.get_variables()
        self._vars.extend(x for x in self._right.get_variables()
                          if x not in self._vars)
        # compute degree
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

    def get_variables(self):
        return self._vars

    def get(self, variables, number, expressions):
        """
        variables: dictionary which keys are the variables name.
        number: class of numbers (e.g for ppl use Linear_Expression, for z3 use Real
        """
        e1 = self._left.get(variables, number, expressions)
        e2 = self._right.get(variables, number, expressions)
        if self._op == "-":
            exp = e1 - e2
        elif self._op == "+":
            exp = e1 + e2
        elif self._op == "*":
            exp = (e2 * e1)
        elif self._op == "/":
            exp = e1 / e2
        return exp

    def transform(self, variables, lib="ppl"):
        """
        variables: list of variables (including prime and local variables)
        lib: "z3" or "ppl"
        """
        if lib == "ppl":
            from ppl import Linear_Expression
            from ppl import Variable

            def toVar(v):
                if v in variables:
                    return Variable(variables.index(v))
                else:
                    raise ValueError("{} is not a variable.".format(v))

            return self.get(toVar, int, Linear_Expression)
        elif lib == "z3":

            def nope(v):
                return v

            from z3 import Real

            def toVar(v):
                if v in variables:
                    return Real(variables.index(v))
                else:
                    raise ValueError("{} is not a variable.".format(v))

            return self.get(toVar, Real, nope)
        else:
            raise ValueError("lib ({}) not supported".format(lib))

    def __add__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(self, "+", right)

    def __sub__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(self, "-", right)

    def __mul__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(self, "*", right)

    def __truediv__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(self, "/", right)

    def __neg__(self):
        return self * (-1)

    def __pos__(self):
        return self

    def __radd__(self, other):
        left = other
        if isinstance(other, (float, int)):
            left = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(left, "+", self)

    def __rsub__(self, other):
        left = other
        if isinstance(other, (float, int)):
            left = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(left, "-", self)

    def __rmul__(self, other):
        left = other
        if isinstance(other, (float, int)):
            left = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(left, "*", self)

    def __rtruediv__(self, other):
        left = other
        if isinstance(other, (float, int)):
            left = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(left, "/", self)

    def __lt__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return inequality(self, "<", right)

    def __le__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return inequality(self, "<=", right)

    def __eq__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return inequality(self, "==", right)

    def __gt__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return inequality(self, ">", right)

    def __ge__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return inequality(self, ">=", right)

    def toString(self, variables=None):
        aux = self._left.toString(variables)
        if self._op:
            r = "{} {}".format(self._op, self._right.toString(variables))
            if aux == "0":
                if self._op in ["+", "-"]:
                    aux = r
                else:
                    aux = "0"
            else:
                aux += " " + r 
        return "({})".format(aux)

    def __repr__(self):
        return self.toString()


class ExprTerma(Expression):

    def __init__(self, word):
        if isinstance(word, (float, int)):
            self.value = word
            self.elem = "number"
        else:
            try:
                self.value = int(word)
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

    def get_variables(self):
        if self.elem == "number":
            return []
        else:
            return [self.value]

    def get(self, variables, number, _expressions):
        if self.elem == "number":
            try:
                return number(self.value)
            except Exception:
                return number(str(self.value))
        else:
            return variables(self.value)

    def __neg__(self):
        if self.elem == "number":
            return ExprTerm(-self.value)
        else:
            return self * (-1)

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
        return "not(" + str(self._exp) + ")"

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
        return dnf_left + dnf_right

    def __repr__(self):
        return str(self._left) + "->" + str(self._right)

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
                new_head += [c + exp for c in head]
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


class inequality(BoolExpression):

    def __init__(self, left, op, right):
        oposite = {"<":">", "<=":">=", "=<":">=", "=":"=", "==":"==", ">=":"<=", "=>":"<="}
        if(not isinstance(left, Expression) or
           not isinstance(right, Expression) or
           not(op in ["<", "<=", "=<", "=", "==", "=>", ">=", ">"])):
            raise ValueError()
        if False and op in ["<", "<=", "=<"]:
            a_left = right
            a_op = oposite[op]
            a_right = left
        else:
            a_left = left
            a_op = op
            a_right = right
        exp = a_left - a_right
        neg = True
        for c, _ in exp._summands:
            if c > 0:
                neg = False
                break
        if neg:
            exp = 0 - exp
            a_op = oposite[a_op]
        self._exp = exp
        self._op = a_op
        self._vars = self._exp.get_variables()
        self._degree = self._exp.degree()

    def get_independent_term(self):
        return self._exp.get_coeff()

    def negate(self):
        zero = ExprTerm(0)
        if self._op in ["=", "=="]:
            return Or(inequality(self._exp, "<", zero),
                      inequality(self._exp, ">", zero))
        elif self._op == ">":
            op = "<="
        elif self._op in [">=", "=>"]:
            op = "<"
        elif self._op == "<":
            op = ">="
        elif self._op in ["<=", "=<"]:
            op = ">"
        return inequality(self._exp, op, zero)

    def toString(self, toVar, number, eq_symb="==", leq_symb="<=", geq_symb=">=", lt_symb="<", gt_symb=">"):
        act_op = str(self._op)
        if act_op in ["=", "=="]:
            op = eq_symb
        elif act_op in ["<=", "=<"]:
            op = leq_symb
        elif act_op in [">=", "=>"]:
            op = geq_symb
        elif act_op == "<":
            op = lt_symb
        else:
            op = gt_symb
        return "{} {} 0".format(self._exp.toString(toVar, number), op)

    def __repr__(self):
        return self.toString(str, int, eq_symb="==", leq_symb="<=", geq_symb=">=", lt_symb="<", gt_symb=">")

    def toDNF(self):
        return [[self]]

    def isFalse(self):
        return False

    def isTrue(self):
        return False

    def isequality(self):
        if self._op in ["=", "=="]:
            return True
        return False

    def get(self, variables, number, expressions):
        left = self._exp.get(variables, number, expressions)
        if isinstance(left, number):
            left = expressions(left)
        zero = expressions(number(0))
        if self._op in ["=", "=="]:
            return (left == zero)
        elif self._op == ">":
            return (left >= expressions(number(1)))
        elif self._op in [">=", "=>"]:
            return (left >= zero)
        elif self._op == "<":
            return (left <= expressions(number(-1)))
        elif self._op in ["<=", "=<"]:
            return (left <= zero)

    def isolate(self, variable):
        """
        returns the expression that corresponds to:
        variable = expression without variable 
        if it is not equality raises a ValueError
        if the term with the variable has degree > 1 raises a ValueError 
        """
        if self._op not in ["=", "=="]:
            raise ValueError("isolate is only for equalities")
        var_coeff = self._exp.get_coeff(variable)
        if var_coeff == 0:
            return None
        if var_coeff != 1 and var_coeff != -1:
            raise ValueError("isolate can not divide by var coeffs")
        var_exp = Expression(var_coeff, "*", variable)
        exp = (self._exp - var_exp) / (-var_coeff)
        if variable in exp.get_variables():
            raise ValueError("degree > 1")
        return exp
    
    def degree(self):
        return self._exp.degree()
    
    def is_linear(self):
        return self._exp.degree() < 2

    def get_variables(self):
        return self._exp.get_variables()

    def transform(self, variables, lib="ppl"):
        """
        variables: list of variables (including prime and local variables)
        lib: "z3" or "ppl"
        """
        if lib == "ppl":
            from ppl import Linear_Expression
            from ppl import Variable

            def toVar(v):
                if v in variables:
                    return Variable(variables.index(v))
                else:
                    raise ValueError("{} is not a variable.".format(v))

            return self.get(toVar, int, Linear_Expression)
        elif lib == "z3":

            def nope(v):
                return v

            from z3 import Real

            def toVar(v):
                if v in variables:
                    return Real(v)
                else:
                    raise ValueError("{} is not a variable.".format(v))

            return self.get(toVar, Real, nope)
        else:
            raise ValueError("lib ({}) not supported".format(lib))


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
            return inequality("0", ">=", "0").toDNF()
        return inequality("0", ">=", "1").toDNF()

    def __repr__(self):
        return self._w

    def isFalse(self):
        return self._w == "false"

    def isTrue(self):
        return self._w == "true"
