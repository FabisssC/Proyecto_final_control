import numpy as np
import pandas as pd

df = pd.read_csv("outputs/identificacion_escalon.csv")

u = df["u_remi"].values
y = df["Ce_remi"].values

Y = y[2:]
Phi = np.vstack([
    y[1:-1],
    y[:-2],
    u[1:-1],
    u[:-2],
]).T

theta, _, _, _ = np.linalg.lstsq(Phi, Y, rcond=None)

a1, a2, b0, b1 = theta

print("a1 =", a1)
print("a2 =", a2)
print("b0 =", b0)
print("b1 =", b1)