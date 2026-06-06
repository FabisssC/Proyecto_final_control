def compute_lbm(weight, height, gender):
    """
    Lean Body Mass según Janmahasatian (2005).
    Misma implementación que AReS simulator.py línea 555-557.

    weight : kg
    height : cm
    gender : 0 = mujer, 1 = hombre  (convención AReS)
    """
    bmi = weight / (height / 100) ** 2
    num = 9.27 * 1000 * weight
    den = 6.68 * 1000 + 216 * bmi if int(gender) == 0 else 8.78 * 1000 + 244 * bmi
    return num / den