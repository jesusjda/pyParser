class BoolExpression(object):

    def __init__(self, params):
        raise NotImplementedError()

    def toDNF(self):
        raise NotImplementedError()

    def negate(self):
        raise NotImplementedError()