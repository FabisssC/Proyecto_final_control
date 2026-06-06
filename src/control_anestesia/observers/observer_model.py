import numpy as np
import control as ct
from control_anestesia.utils.pk_params import compute_lbm


def build_observer_model(h_min=5/60, age=40, weight=54, height=163, gender=0):
    """
    Construye las matrices discretas del modelo PK para propofol y remifentanilo.
    Parámetros calculados con Schnider (propofol) y Minto (remifentanilo).
    Misma convención de género que AReS: 0=mujer, 1=hombre.
    """
    LBM = compute_lbm(weight, height, gender)

    # Propofol — Schnider
    V1p = 4.27
    V2p = 18.9 - 0.391 * (age - 53)
    V3p = 2.38
    C1p = 0.0456*(weight-77) - 0.0681*(LBM-59) + 0.0264*(height-177) + 1.89
    C2p = 1.29 - 0.024*(age-53)
    C3p = 0.836
    k12p = C2p/V1p;  k13p = C3p/V1p;  k10p = C1p/V1p
    k21p = C2p/V2p;  k31p = C3p/V3p;  ke0p = 0.456
    kkp  = -k10p - k12p - k13p

    # Remifentanilo — Minto
    V1r = 5.1  - 0.0201*(age-40) + 0.072*(LBM-55)
    V2r = 9.82 - 0.0811*(age-40) + 0.108*(LBM-55)
    V3r = 5.42
    C1r = 2.6  - 0.0162*(age-40) + 0.0191*(LBM-55)
    C2r = 2.05 - 0.0301*(age-40)
    C3r = 0.076 - 0.00113*(age-40)
    k12r = C2r/V1r;  k13r = C3r/V1r;  k10r = C1r/V1r
    k21r = C2r/V2r;  k31r = C3r/V3r
    ke0r = 0.595 - 0.007*(age-40)
    kkr  = -k10r - k12r - k13r

    Aprop = np.array([
        [kkp,   k21p,  k31p,   0.0],
        [k12p, -k21p,  0.0,    0.0],
        [k13p,  0.0,  -k31p,   0.0],
        [ke0p,  0.0,   0.0,  -ke0p],
    ], dtype=float)
    Bprop = np.array([[1.0],[0.0],[0.0],[0.0]])

    Arem = np.array([
        [kkr,   k21r,  k31r,   0.0],
        [k12r, -k21r,  0.0,    0.0],
        [k13r,  0.0,  -k31r,   0.0],
        [ke0r,  0.0,   0.0,  -ke0r],
    ], dtype=float)
    Brem = np.array([[1.0],[0.0],[0.0],[0.0]])

    A = np.block([[Aprop, np.zeros((4,4))],[np.zeros((4,4)), Arem]])
    B = np.block([[Bprop, np.zeros((4,1))],[np.zeros((4,1)), Brem]])
    C = np.array([[0,0,0,1,0,0,0,0],[0,0,0,0,0,0,0,1]], dtype=float)
    D = np.zeros((2,2))

    sys_d = ct.c2d(ct.ss(A, B, C, D), h_min, method="zoh")
    return (
        np.asarray(sys_d.A),
        np.asarray(sys_d.B),
        np.asarray(sys_d.C),
        np.asarray(sys_d.D),
    )