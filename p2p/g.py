D_MAP = {}
R_LIS = set()


def can(piece, peer):
    pr = D_MAP.get(piece, None)
    if pr is None:
        D_MAP[piece] = peer
        return True
    else:
        return pr is peer


def rm(piece):
    del D_MAP[piece]


def can_r(peer, index, begin):
    item = (peer, index, begin)
    if item in R_LIS:
        return False
    else:
        R_LIS.add(item)
        return True


def rm_r(peer, index, begin):
    item = (peer, index, begin)
    if item in R_LIS:
        R_LIS.remove(item)
