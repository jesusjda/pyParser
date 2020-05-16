
def is_notdeterministic(cons, gvars, usedvs={}):
    N = int(len(gvars) / 2)
    _vars, _pvars = gvars[:N], gvars[N:]
    pending = [v for v in _pvars if usedvs.get(v,True)]
    for c in cons:
        pv = False
        vs = c.get_variables()
        for v in vs:
            if not usedvs.get(v, True):
                continue
            if v in _pvars:
                if not c.is_equality():
                    return True
                if v in pending:
                    pending.remove(v)
                if pv:
                    return True
                pv = True
                cf = c.get_coefficient(v)
                if cf != 1 and cf != -1:
                    return True
            elif v not in _vars:
                return True
    if len(pending) > 0:
        return True
    return False


def used_vars(trs, gvars):
    from genericparser import constants
    N = int(len(gvars) / 2)
    _vars, _pvars = gvars[:N], gvars[N:]
    unused = gvars[:]
    used = {v: False for v in gvars}
    for tr in trs:
        if len(unused) == 0:
            break
        for c in tr[constants.transition.constraints]:
            if len(unused) == 0:
                break
            vs = c.get_variables()
            if len(vs) == 0:
                continue
            elif c.is_equality() and len(vs) == 2:
                if vs[0] in gvars and vs[1] in gvars:
                    i1 = gvars.index(vs[0])
                    i2 = gvars.index(vs[1])
                    if i1 - i2 == N or i2 - i1 == N:
                        continue
            for v in vs:
                if v not in gvars:
                    continue
                i1 = gvars.index(v)
                i2 = (i1 + N) % (2 * N)
                if v in unused:
                    unused.remove(v)
                if gvars[i2] in unused:
                    unused.remove(gvars[i2])
                used[v] = True
                used[gvars[i2]] = True
    return used

