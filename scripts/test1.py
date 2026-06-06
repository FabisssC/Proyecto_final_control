import numpy as np
from control_anestesia.observers.observer_model import build_observer_model

Ap, Bp, Cp, Dp = build_observer_model(
    h_min=5/60, age=74, weight=65, height=151, gender=1
)

Ld = np.array([
    [ 0.0,     1 ],   # fila 0: compartimento central propofol
    [ 0.0,     0.0 ],
    [ 0.0,    0.0 ],
    [-1.83,    0 ],   # fila 3: sitio de efecto propofol
    [ 0,     0.0 ],   # fila 4: compartimento central remifentanilo
    [ 0.0,     0.0],
    [ 0.000,  0.0 ],
    [ 0.0,    -1.95],
], dtype=float)

A_obs = Ap + Ld @ Cp  # ← signo + porque la convención es y_est - y_med

eigenvalues = np.linalg.eigvals(A_obs)
print("Valores propios:")
for ev in eigenvalues:
    print(f"  |ev|={abs(ev):.6f}  →  {'OK' if abs(ev) < 1 else 'INESTABLE'}")

off_diag = A_obs - np.diag(np.diag(A_obs))
metzler_ok = np.all(off_diag >= -1e-10)
print(f"\nMetzler: {'OK' if metzler_ok else 'VIOLADA'}")
if not metzler_ok:
    rows, cols = np.where(off_diag < -1e-10)
    for r, c in zip(rows, cols):
        print(f"  A_obs[{r},{c}] = {off_diag[r,c]:.6f}")