import numpy as np
import pandas as pd
from scipy.optimize import least_squares

df = pd.read_csv("outputs/run_pid_observer.csv")

u = df["u_remi_app"].values
y_real = df["Ce_remi"].values
N = len(u)

# Modelo 2 estados
def simulate(params):
    a1, a2, b1, b2, g = params

    x1 = 0.0
    x2 = 0.0

    y_pred = np.zeros(N)

    for k in range(N):
        x1 = a1 * x1 + b1 * u[k]
        x2 = a2 * x2 + b2 * x1
        y_pred[k] = g * x2

    return y_pred

def residuals(params):
    y_pred = simulate(params)
    return y_pred - y_real

# Inicial (importante)
params0 = [0.9, 0.9, 0.1, 0.1, 1.0]

# Restricciones de estabilidad
lower = [0.0, 0.0, 0.0, 0.0, 0.0]
upper = [1.0, 1.0, 10.0, 10.0, 10.0]

res = least_squares(residuals, params0, bounds=(lower, upper))

a1, a2, b1, b2, g = res.x

print("a1 =", a1)
print("a2 =", a2)
print("b1 =", b1)
print("b2 =", b2)
print("g  =", g)

# Validación rápida
import matplotlib.pyplot as plt

y_pred = simulate(res.x)

plt.plot(df["time_min"], y_real, label="AReS")
plt.plot(df["time_min"], y_pred, "--", label="modelo 2 estados")
plt.legend()
plt.show()