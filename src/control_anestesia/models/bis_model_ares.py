import numpy as np

def bis_from_ce_ares(ce_bis, ce_remi, age=40):
    e0 = 93.0
    beta = 1.0

    ec50_prop = 3.08 * np.exp(-0.00635 * (age - 35))
    ec50_remi = 12.7

    ce_bis = max(float(ce_bis), 0.0)
    ce_remi = max(float(ce_remi), 0.0)

    inter_prop = ce_bis / ec50_prop
    inter_remi = ce_remi / ec50_remi

    theta = inter_prop / (inter_prop + inter_remi + np.finfo(float).eps)
    inter = (inter_prop + inter_remi) / (1 - beta * theta + beta * theta**2)

    if inter < 0:
        inter = 0.0

    gamma = 1.89 if ce_bis < ec50_prop else 1.47

    effect = inter**gamma / (1 + inter**gamma)
    bis = e0 - e0 * effect

    return bis