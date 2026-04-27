import numpy as np
import control as ct


def build_observer_model(h_min=5 / 60):
    A_age = 40
    W = 54
    H = 163

    LBM = 1.07 * W - 148 * (W / H) ** 2

    V1p = 4.27
    V2p = 18.9 - 0.391 * (A_age - 53)
    V3p = 2.38
    C1p = 0.0456 * (W - 77) - 0.0681 * (LBM - 59) + 0.0264 * (H - 177) + 1.89
    C2p = 1.29 - 0.024 * (A_age - 53)
    C3p = 0.836

    k12p = C2p / V1p
    k13p = C3p / V1p
    k10p = C1p / V1p
    k21p = C2p / V2p
    k31p = C3p / V3p
    ke0p = 0.456
    kkp = -k10p - k12p - k13p

    V1r = 5.1 - 0.0201 * (A_age - 40) + 0.072 * (LBM - 55)
    V2r = 9.82 - 0.0811 * (A_age - 40) + 0.108 * (LBM - 55)
    V3r = 5.42
    C1r = 2.6 - 0.0162 * (A_age - 40) + 0.0191 * (LBM - 55)
    C2r = 2.05 - 0.0301 * (A_age - 40)
    C3r = 0.076 - 0.00113 * (A_age - 40)

    k12r = C2r / V1r
    k13r = C3r / V1r
    k10r = C1r / V1r
    k21r = C2r / V2r
    k31r = C3r / V3r
    ke0r = 0.595 - 0.007 * (A_age - 40)
    kkr = -k10r - k12r - k13r

    Aprop = np.array([
        [kkp,   k21p,   k31p,   0.0],
        [k12p, -k21p,   0.0,    0.0],
        [k13p,  0.0,   -k31p,   0.0],
        [ke0p,  0.0,    0.0,   -ke0p],
    ], dtype=float)

    Bprop = np.array([[1.0], [0.0], [0.0], [0.0]])

    Arem = np.array([
        [kkr,   k21r,   k31r,   0.0],
        [k12r, -k21r,   0.0,    0.0],
        [k13r,  0.0,   -k31r,   0.0],
        [ke0r,  0.0,    0.0,   -ke0r],
    ], dtype=float)

    Brem = np.array([[1.0], [0.0], [0.0], [0.0]])

    A = np.block([
        [Aprop, np.zeros((4, 4))],
        [np.zeros((4, 4)), Arem],
    ])

    B = np.block([
        [Bprop, np.zeros((4, 1))],
        [np.zeros((4, 1)), Brem],
    ])

    C = np.array([
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1],
    ], dtype=float)

    D = np.zeros((2, 2))

    sys_c = ct.ss(A, B, C, D)
    sys_d = ct.c2d(sys_c, h_min, method="zoh")

    return (
        np.asarray(sys_d.A),
        np.asarray(sys_d.B),
        np.asarray(sys_d.C),
        np.asarray(sys_d.D),
    )