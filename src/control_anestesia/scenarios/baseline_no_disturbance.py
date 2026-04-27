import numpy as np


def escenario_base(Ts_s=5, duracion_min=60):
    t_sim = int((duracion_min * 60) / Ts_s)

    # Escenario activo: infusión constante
    u_prop = np.full(t_sim, 6.0)    # mg/s
    u_remi = np.full(t_sim, 12.0)   # µg/s

    # Escenario alternativo 1: dosis menor
    # u_prop = np.full(t_sim, 4.0)
    # u_remi = np.full(t_sim, 8.0)

    # Escenario alternativo 2: perfil escalonado simple
    # cambio = int((10 * 60) / Ts_s)
    # u_prop = np.concatenate([
    #     np.full(cambio, 8.0),
    #     np.full(t_sim - cambio, 4.0)
    # ])
    # u_remi = np.concatenate([
    #     np.full(cambio, 14.0),
    #     np.full(t_sim - cambio, 8.0)
    # ])

    return u_prop, u_remi
