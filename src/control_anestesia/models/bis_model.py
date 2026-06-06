import numpy as np

_DEFAULT_PD = dict(
    Ce50p=6.33, Ce50r=12.5, gamma=2.24,
    beta=2.00, E0=98.8, Emax=94.10
)

def make_bis_model(patient_profile=None, demographics=None):
    """
    Devuelve una función bis_from_ce configurada para el paciente activo.

    Prioridad:
    1. patient_profile con clave "pd" → parámetros directos del artículo
    2. demographics de AReS → Ce50p estimado desde edad (Eleveld simplificado)
    3. None → defaults del Paciente 1
    """
    if patient_profile is not None and "pd" in patient_profile:
        params = {**_DEFAULT_PD, **patient_profile["pd"]}

    elif demographics is not None:
        age = demographics["age"]
        ce50p = 3.08 * np.exp(-0.00635 * (age - 35))
        params = {**_DEFAULT_PD, "Ce50p": ce50p}

    else:
        params = _DEFAULT_PD

    def bis_from_ce(Ce_prop, Ce_remi):
        Ce_prop = max(float(Ce_prop), 0.0)
        Ce_remi = max(float(Ce_remi), 0.0)

        Yp   = Ce_prop / params["Ce50p"]
        Yr   = Ce_remi / params["Ce50r"]
        Utot = Yp + Yr

        if Utot <= 1e-12:
            return params["E0"]

        phi    = Yp / Utot
        U50    = 1 - params["beta"] * phi + params["beta"] * phi ** 2
        z      = min(max(Utot / U50, 0.0), 1e6)
        effect = (z ** params["gamma"]) / (1 + z ** params["gamma"])
        return params["E0"] - params["Emax"] * effect

    return bis_from_ce