from enum import Enum

class BoolExpression(object):

    def __init__(self, params): raise NotImplementedError()

    def to_DNF(self): raise NotImplementedError()

    def negate(self): raise NotImplementedError()

    def is_true(self): raise NotImplementedError()

    def is_false(self): raise NotImplementedError()

    def toString(self, toVar, toNum, eq_symb="==", leq_symb="<=", geq_symb=">=", lt_symb="<", gt_symb=">"): raise NotImplementedError()

    def degree(self): raise NotImplementedError()

    def get_variables(self): raise NotImplementedError()

    def is_linear(self):
        return self.degree() < 2
    
    def is_equality(self):
        return False

    def __repr__(self):
        return self.toString(str, int, eq_symb="==", leq_symb="<=", geq_symb=">=", lt_symb="<", gt_symb=">")

class Not(BoolExpression):

    def __init__(self, exp):
        if isinstance(exp, BoolExpression):
            self._exp = exp
        else:
            raise ValueError()

    def negate(self): return self._exp

    def toDNF(self):
        neg_exp = self._exp.negate()
        return neg_exp.toDNF()

    def __repr__(self):
        return "not(" + str(self._exp) + ")"

    def isTrue(self):
        return self._exp.isFalse()

    def isFalse(self):
        return self._exp.isTrue()

class opCMP(Enum):
    LT="<"
    LEQ="<="
    GT=">"
    GEQ=">="
    EQ="=="
    NEQ="!="
    
    def oposite(self):
        if self == opCMP.LT:
            return opCMP.GT
        if self == opCMP.GT:
            return opCMP.LT
        if self == opCMP.LEQ:
            return opCMP.GEQ
        if self == opCMP.GEQ:
            return opCMP.LEQ
        return self
    
    def complement(self):
        if self == opCMP.LT:
            return opCMP.GEQ
        if self == opCMP.GT:
            return opCMP.LEQ
        if self == opCMP.LEQ:
            return opCMP.GT
        if self == opCMP.GEQ:
            return opCMP.LT
        if self == opCMP.EQ:
            return opCMP.NEQ
        if self == opCMP.NEQ:
            return opCMP.EQ

class opExp(Enum):
    ADD="+"
    SUB="-"
    MUL="*"
    DIV="/"

class Constraint(BoolExpression):

    def __init__(self, left: Expression, op: opCMP, right: Expression = None):
        if(not isinstance(left, Expression) or
           (right is not None and not isinstance(right, Expression)) or
           (not isinstance(op, opCMP))):
            raise ValueError()
        exp = left
        a_op = op
        if right is not None:
            exp = exp - right
        neg = True
        for c, _ in exp._summands:
            if c > 0:
                neg = False
                break
        if neg:
            exp = 0 - exp
            a_op = a_op.oposite()
        self._exp = exp
        self._op = a_op
        self._vars = self._exp.get_variables()
        self._degree = self._exp.degree()            

    def to_DNF(self): return Or(And(self))

    def negate(self):
        zero = ExprTerm(0)
        if self._op == opCMP.EQ:
            return Or(Constraint(self._exp, opCMP.GT, zero),
                      Constraint(self._exp, opCMP.LT, zero))
        return Constraint(self._exp, self._op.complement(), zero)

    def is_true(self): return False

    def is_false(self): return False
    
    def is_equality(self): return self._op == opCMP.EQ    
    
    def degree(self): return self._degree

    def get_variables(self): return self._vars

    def get_independent_term(self): return self._exp.get_coeff()

    def toString(self, toVar, toNum, eq_symb="==", leq_symb="<=", geq_symb=">=", lt_symb="<", gt_symb=">"): raise NotImplementedError()

class BoolTerm(Enum, BoolExpression):
    TRUE="true"
    FALSE="false"
    
    def to_DNF(self):
        if self == BoolTerm.TRUE:
            return Or(And(Constraint(ExprTerm(0), "==")))
        return Or(And(Constraint(ExprTerm(1), "==")))

    def negate(self):
        if self == BoolTerm.TRUE:
            return BoolTerm.FALSE
        return BoolTerm.TRUE

    def is_true(self): return self == BoolTerm.TRUE

    def is_false(self): return self == BoolTerm.FALSE
    
    def degree(self): return 0

    def get_variables(self): return []

    def toString(self, toVar, toNum, eq_symb="==", leq_symb="<=", geq_symb=">=", lt_symb="<", gt_symb=">"): raise NotImplementedError()

class Expression(object):
    
    def __init__(self, left: Expression, op: opExp, right: Expression):
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
        if not isinstance(op, opExp):
            raise ValueError("{} is not a valid Operation.".format(op))
        from collections import Counter
        summands = []
        max_degree = 0
        n_vs = []
        if op == opExp.DIV:
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
                max_degree = left.degree()
                n_vs = left.get_variables()
        elif op == opExp.MUL:
            tmp_summands = []
            for l_s in left._summands:
                l_coeff, l_vars = l_s
                for l_r in right._summands:
                    coeff = l_coeff * l_r[0]
                    var = l_vars + l_r[1]
                    var.sort()
                    if coeff != 0:
                        tmp_summands.append((coeff, var))
            var_set = set()
            while len(tmp_summands) > 0:
                coeff, vs = tmp_summands.pop(0)
                for sr in tmp_summands:
                    if Counter(vs) == Counter(sr[1]):
                        coeff += sr[0]
                        tmp_summands.remove(sr)
                if coeff != 0:
                    if len(vs) > max_degree:
                        max_degree = len(vs)
                    var_set.union(vs)
                    summands.append((coeff, vs))
            n_vs = list(var_set)
            del var_set
        elif op in [opExp.ADD,opExp.SUB]:
            symb = 1
            if op == opExp.SUB:
                symb = -1
            pending_summands = right._summands
            var_set = set()
            for s in left._summands:
                coeff, vs = s
                for sr in pending_summands:
                    if Counter(vs) == Counter(sr[1]):
                        coeff += symb * sr[0]
                        pending_summands.remove(sr)
                if coeff != 0:
                    if len(vs) > max_degree:
                        max_degree = len(vs)
                    var_set.union(vs)
                    summands.append((coeff, vs))
            for coeff, vs in pending_summands:
                if coeff != 0:
                    if len(vs) > max_degree:
                        max_degree = len(vs)
                    var_set.union(vs)
                    summands.append((symb * coeff, vs))
            n_vs = list(var_set)
            del var_set
        self._summands = summands
        self._degree = max_degree
        self._vars = n_vs

    def degree(self): return self._degree
    
    def is_linear(self): return self.degree() < 2

    def get_variables(self): return self._vars
    
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

    def __repr__(self): return self.toString(str, int)
    
    def get(self, toVar, toNum, toExp, ignore_zero=False):
        """
        variables: dictionary which keys are the variables name.
        number: class of numbers (e.g for ppl use Linear_Expression, for z3 use Real
        """
        exp = toExp(0)
        for s in self._summands:
            s_exp = toNum(s[0])
            if ignore_zero:
                if s_exp == toNum(0):
                    continue
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

            from z3 import Int
            def toNum(v):
                return Int(int(v))
            def toVar(v):
                if v in variables:
                    return Int(v)
                else:
                    raise ValueError("{} is not a variable.".format(v))

            return self.get(toVar, toNum, nope, ignore_zero=True)
        else:
            raise ValueError("lib ({}) not supported".format(lib))

    def __add__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(self, opExp.ADD, right)

    def __sub__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(self, opExp.SUB, right)

    def __mul__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(self, opExp.MUL, right)

    def __truediv__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(self, opExp.DIV, right)

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
        return Expression(left, opExp.ADD, self)

    def __rsub__(self, other):
        left = other
        if isinstance(other, (float, int)):
            left = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(left, opExp.SUB, self)

    def __rmul__(self, other):
        left = other
        if isinstance(other, (float, int)):
            left = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(left, opExp.MUL, self)

    def __rtruediv__(self, other):
        left = other
        if isinstance(other, (float, int)):
            left = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Expression(left, opExp.DIV, self)

    def __lt__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Constraint(self, opCMP.LT, right)

    def __le__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Constraint(self, opCMP.LEQ, right)

    def __eq__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Constraint(self, opCMP.EQ, right)

    def __gt__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Constraint(self, opCMP.GT, right)

    def __ge__(self, other):
        right = other
        if isinstance(other, (float, int)):
            right = ExprTerm(other)
        elif not isinstance(other, (ExprTerm, Expression)):
            raise NotImplementedError()
        return Constraint(self, opCMP.GEQ, right)


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
        self._degree = len(vs)
        self._vars = list(vs)

    def __neg__(self):
        return self * (-1)




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
        return "(" + " /\ ".join(s) + ")"

    def isTrue(self):
        for e in self._boolexps:
            if not e.isTrue():
                return False
        return True

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
        return "(" + " \/ ".join(s) + ")"


class ConstraintOLD(BoolExpression):



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

            return self.get(toVar, int, nope)
        else:
            raise ValueError("lib ({}) not supported".format(lib))
