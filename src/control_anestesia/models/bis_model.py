import numpy as np


def bis_from_ce(Ce_prop, Ce_remi):
    Ce50p = 6.33
    Ce50r = 12.5
    gamma = 2.24
    beta = 2.00
    E0 = 98.8
    Emax = 94.10

    Ce_prop = max(float(Ce_prop), 0.0)
    Ce_remi = max(float(Ce_remi), 0.0)

    Yp = Ce_prop / Ce50p
    Yr = Ce_remi / Ce50r

    Utot = Yp + Yr

    if Utot <= 1e-12:
        return E0

    phi = Yp / Utot
    U50 = 1 - beta * phi + beta * phi * phi

    z = Utot / U50
    z = min(max(z, 0.0), 1e6)

    effect = (z ** gamma) / (1 + z ** gamma)
    bis = E0 - Emax * effect

    return bis