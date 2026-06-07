"""
serial_pump.py  –  Interfaz Python ↔ ESP32 para bombas de anestesia
====================================================================

ANÁLISIS DEL PROBLEMA (diagnóstico vs App Designer MATLAB):
────────────────────────────────────────────────────────────
MATLAB App Designer usa mapeo proporcional con PISO para remifentanilo:
    sp_p = (u_next(2)/0.0308) * (154-35)/217.27 + 35
    → Garantiza RPM_min=35 aunque u→0. Por eso la peristáltica funciona.

Para propofol MATLAB NO tiene ese piso:
    sp_j = u_next(1)/0.48951
    → En mantenimiento (u~0.37) → sp_j~0.76 RPM → motor tampoco mueve bien.

Python (AReS, TCI OFF) entrega:
    u_prop [mg/s]  - pico inducción ~1.5 mg/s, mantenimiento ~0.05 mg/s
    u_remi [μg/s]  - pico inducción ~5.8 μg/s, mantenimiento ~0.10 μg/s

LIMITACIÓN FÍSICA real de la jeringa (propofol):
    RPM_J_MIN = 7.944 → flow_min = 0.4543*7.944 + 0.2116 = 3.82 mL/min
    Para 10 mg/mL: u_prop_min = 3.82/60 * 10 = 0.637 mg/s
    → Para u_prop < 0.637 mg/s el motor no puede mover la jeringa.
    → Mantenimiento (0.05 mg/s) = 8x por debajo del mínimo físico.

SOLUCIONES implementadas aquí:
    1. Conversión física correcta (mg/s→mL/min→RPM) con saturación.
    2. Mapeo proporcional con piso/techo (replica estrategia MATLAB).
    3. La elección entre modos se hace con el parámetro `mode`.

RECOMENDACIÓN para hardware actual:
    mode="proportional" → replica MATLAB, bombas siempre en movimiento.
    mode="physical"     → conversión exacta, jeringa se detiene en mantenimiento
                          (limitación real, no error de código).

Para resolver físicamente: diluir propofol a 2 mg/mL (5x dilución)
→ flow_mantenimiento = 1.5 mL/min, mucho más cercano al mínimo de la bomba.
"""

import math
import time
import serial
import numpy as np


# ── Concentraciones de solución ──────────────────────────────────────────────
C_PROP_MG_ML = 10.0    # mg/mL  (Propofol 1% estándar)
C_REMI_UG_ML = 50.0    # μg/mL  (Remifentanilo estándar)

# ── Calibración dinámica (Tablas 6-7, ProtocoloFinal, OLS sobre datos reales) ─
# Jeringa (propofol) — OLS sobre 13 puntos Tabla 7
#   R² = 0.9860  |  error medio = 0.169 mL/min  |  error max = 0.359 mL/min
K_J = 0.416938   # (mL/min)/RPM
B_J = -1.415080  # mL/min  (intercepto negativo: el modelo lineal no pasa por el origen)

# Peristáltica (remifentanilo) — OLS sobre 17 puntos Tabla 6
#   R² = 0.9984  |  error medio = 0.051 mL/min  |  error max = 0.117 mL/min
K_P = 0.039281   # (mL/min)/RPM
B_P = -0.028832  # mL/min

RPM_J_MIN = 7.944   # PWM 40% (mínimo físico jeringa)
RPM_J_MAX = 20.1    # PWM 100%
RPM_P_MIN = 33.2    # PWM 20% (mínimo físico peristáltica)
RPM_P_MAX = 166.0   # PWM 100%

# ── Constante firmware ESP32 (K_JERINGA en bombas_control.ino) ────────────────
K_J_FIRMWARE = 0.48951   # el ESP32 reporta: rpm1 * K_J_FIRMWARE

# ── Rango de comandos AReS (TCI OFF) para mapeo proporcional ─────────────────
# Kp=0.047 → pico inducción ≈ 2.02 mg/s → se satura al máximo de RPM (correcto)
U_PROP_MAX_MGS = 2.0    # mg/s  (u > 2.0 satura en RPM_J_MAX, comportamiento deseado)
U_REMI_MAX_UGS = 7.0    # μg/s  (cubre inducción con ratio=2 y Kp=0.047)


# ── Funciones de conversión física ───────────────────────────────────────────

def _safe(v: float, fallback: float = 0.0) -> float:
    return fallback if (not math.isfinite(v) or v != v) else v


def prop_physical_rpm(u_prop_mgs: float) -> float:
    """mg/s → RPM jeringa (conversión física exacta, puede dar <RPM_J_MIN)."""
    if u_prop_mgs <= 0.0:
        return 0.0
    flow = (u_prop_mgs / C_PROP_MG_ML) * 60.0    # mL/min
    rpm  = (flow - B_J) / K_J
    return float(np.clip(rpm, 0.0, RPM_J_MAX))


def remi_physical_rpm(u_remi_ugs: float) -> float:
    """μg/s → RPM peristáltica (conversión física exacta)."""
    if u_remi_ugs <= 0.0:
        return 0.0
    flow = (u_remi_ugs / C_REMI_UG_ML) * 60.0    # mL/min
    rpm  = (flow - B_P) / K_P
    return float(np.clip(rpm, 0.0, RPM_P_MAX))


def prop_proportional_rpm(u_prop_mgs: float) -> float:
    """
    mg/s → RPM jeringa con mapeo proporcional con piso/techo.
    Replica la estrategia de App Designer para remifentanilo.
    [0, U_PROP_MAX] → [RPM_J_MIN, RPM_J_MAX]
    Garantiza que si u>0 el motor siempre se mueve.
    """
    if u_prop_mgs <= 0.0:
        return 0.0
    ratio = np.clip(u_prop_mgs / U_PROP_MAX_MGS, 0.0, 1.0)
    return float(RPM_J_MIN + ratio * (RPM_J_MAX - RPM_J_MIN))


def remi_proportional_rpm(u_remi_ugs: float) -> float:
    """
    μg/s → RPM peristáltica con mapeo proporcional (idéntico a MATLAB).
    [0, U_REMI_MAX] → [RPM_P_MIN, RPM_P_MAX]
    """
    if u_remi_ugs <= 0.0:
        return 0.0
    ratio = np.clip(u_remi_ugs / U_REMI_MAX_UGS, 0.0, 1.0)
    return float(RPM_P_MIN + ratio * (RPM_P_MAX - RPM_P_MIN))


def rpm_to_prop_mgs(rpm_j: float) -> float:
    """RPM jeringa → mg/s propofol via calibración física (modo physical)."""
    if rpm_j <= 0.0:
        return 0.0
    flow = K_J * rpm_j + B_J
    return max(0.0, (flow / 60.0) * C_PROP_MG_ML)


def rpm_to_remi_ugs(rpm_p: float) -> float:
    """RPM peristáltica → μg/s remi via calibración física (modo physical)."""
    if rpm_p <= 0.0:
        return 0.0
    flow = K_P * rpm_p + B_P
    return max(0.0, (flow / 60.0) * C_REMI_UG_ML)


def rpm_to_prop_mgs_proportional(rpm_j: float) -> float:
    """
    RPM jeringa → mg/s propofol via INVERSA del mapeo proporcional.

    Usar en modo 'proportional' para que u_prop_app ≈ u_prop_cmd
    en operación normal, y u_prop_app < u_prop_cmd si la bomba falla.

    Inversa exacta de prop_proportional_rpm():
        u = (RPM - RPM_J_MIN) / (RPM_J_MAX - RPM_J_MIN) * U_PROP_MAX
    """
    if rpm_j < RPM_J_MIN:
        return 0.0
    u = (rpm_j - RPM_J_MIN) / (RPM_J_MAX - RPM_J_MIN) * U_PROP_MAX_MGS
    return float(np.clip(u, 0.0, U_PROP_MAX_MGS))


def rpm_to_remi_ugs_proportional(rpm_p: float) -> float:
    """
    RPM peristáltica → μg/s remi via INVERSA del mapeo proporcional.

    Inversa exacta de remi_proportional_rpm():
        u = (RPM - RPM_P_MIN) / (RPM_P_MAX - RPM_P_MIN) * U_REMI_MAX
    """
    if rpm_p < RPM_P_MIN:
        return 0.0
    u = (rpm_p - RPM_P_MIN) / (RPM_P_MAX - RPM_P_MIN) * U_REMI_MAX_UGS
    return float(np.clip(u, 0.0, U_REMI_MAX_UGS))


# ── Clase principal ───────────────────────────────────────────────────────────

class SerialPumpInterface:
    """
    Interfaz serial Python ↔ ESP32 para bombas de anestesia.

    Parámetros
    ----------
    port          : Puerto serial del ESP32 (ej. "COM3" o "/dev/ttyUSB0")
    baudrate      : 115200 (debe coincidir con bombas_control.ino)
    mode          : "proportional" → mapeo [0,u_max]→[RPM_min,RPM_max]
                    "physical"     → conversión exacta mg/s→mL/min→RPM
    alpha_prop    : EMA para feedback jeringa (propofol).
                    Bomba de jeringa es mecánicamente suave → alpha=0.35 OK.
    alpha_remi    : EMA para feedback peristáltica (remifentanilo).
                    Bomba peristáltica tiene pulsaciones de rodillo → usar
                    alpha más bajo (0.10–0.15) para suprimir el ruido sin
                    perder capacidad de detección de fallos reales.
                    Regla: alpha × Ts_s ≈ 0.5–1 s de constante de tiempo efectiva.
    """

    def __init__(
        self,
        port: str = "COM3",
        baudrate: int = 115200,
        timeout: float = 0.2,
        mode: str = "proportional",
        alpha_prop: float = 0.38,
        alpha_remi: float = 0.35,
    ):
        assert mode in ("proportional", "physical"), \
            "mode debe ser 'proportional' o 'physical'"
        self.port       = port
        self.baudrate   = baudrate
        self.timeout    = timeout
        self.mode       = mode
        self.alpha_prop = alpha_prop
        self.alpha_remi = alpha_remi
        self.ser: serial.Serial | None = None
        self._u_prop_f  = 0.0
        self._u_remi_f  = 0.0

    def connect(self) -> None:
        self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        time.sleep(2)

    def close(self) -> None:
        if self.ser and self.ser.is_open:
            self.stop()
            self.ser.close()

    def stop(self) -> None:
        if self.ser and self.ser.is_open:
            self.ser.write(b"0\n")

    def send_rates(
        self, u_prop_mgs: float, u_remi_ugs: float
    ) -> tuple[float, float]:
        """
        Convierte u_prop [mg/s] y u_remi [μg/s] a RPM y envía al ESP32.

        Retorna (rpm_j, rpm_p) para logging.
        """
        u_prop_mgs = _safe(u_prop_mgs, 0.0)
        u_remi_ugs = _safe(u_remi_ugs, 0.0)

        if self.mode == "proportional":
            rpm_j = prop_proportional_rpm(u_prop_mgs)
            rpm_p = remi_proportional_rpm(u_remi_ugs)
        else:
            rpm_j = prop_physical_rpm(u_prop_mgs)
            rpm_p = remi_physical_rpm(u_remi_ugs)

        self.ser.write(f"sj{rpm_j:.3f}\n".encode())
        time.sleep(0.001)
        self.ser.write(f"sp{rpm_p:.3f}\n".encode())

        return rpm_j, rpm_p

    def read_rates(self) -> tuple[float | None, float | None]:
        """
        Lee feedback del ESP32 y devuelve (u_prop [mg/s], u_remi [μg/s]).

        Filtrado en dos etapas:
          1. Promedio de TODAS las lecturas del paso (box filter).
             ~50 mensajes por paso de 5s → cancela pulsaciones de rodillo.
          2. EMA entre pasos: alpha_prop=0.35, alpha_remi=0.12.

        Retorna (None, None) si no hay datos en este paso.
        """
        all_props: list[float] = []
        all_remis: list[float] = []

        while self.ser.in_waiting > 0:
            line = self.ser.readline().decode(errors="ignore").strip()
            parts = line.split(",")
            if len(parts) == 2:
                try:
                    val_j = float(parts[0])
                    rpm_j = val_j / K_J_FIRMWARE
                    rpm_p = float(parts[1])

                    if self.mode == "proportional":
                        u_p = rpm_to_prop_mgs_proportional(rpm_j)
                        u_r = rpm_to_remi_ugs_proportional(rpm_p)
                    else:
                        u_p = rpm_to_prop_mgs(rpm_j)
                        u_r = rpm_to_remi_ugs(rpm_p)

                    all_props.append(u_p)
                    all_remis.append(u_r)
                except ValueError:
                    pass

        if not all_props:
            return None, None

        # Etapa 1: promedio del paso
        u_p_step = float(np.mean(all_props))
        u_r_step = float(np.mean(all_remis))

        # Etapa 2: EMA entre pasos
        self._u_prop_f = self.alpha_prop * u_p_step + (1 - self.alpha_prop) * self._u_prop_f
        self._u_remi_f = self.alpha_remi * u_r_step + (1 - self.alpha_remi) * self._u_remi_f

        return self._u_prop_f, self._u_remi_f

    def conversion_report(
        self, u_prop_mgs: float, u_remi_ugs: float
    ) -> dict:
        """Diagnóstico completo de la conversión para un par de valores."""
        flow_p = (u_prop_mgs / C_PROP_MG_ML) * 60.0
        flow_r = (u_remi_ugs / C_REMI_UG_ML) * 60.0
        rpm_j_phys = prop_physical_rpm(u_prop_mgs)
        rpm_p_phys = remi_physical_rpm(u_remi_ugs)
        rpm_j_prop = prop_proportional_rpm(u_prop_mgs)
        rpm_p_prop = remi_proportional_rpm(u_remi_ugs)
        return {
            "u_prop_mgs"      : u_prop_mgs,
            "u_remi_ugs"      : u_remi_ugs,
            "flow_prop_ml_min": round(flow_p, 4),
            "flow_remi_ml_min": round(flow_r, 4),
            # Modo físico
            "rpm_j_physical"  : round(rpm_j_phys, 3),
            "rpm_p_physical"  : round(rpm_p_phys, 3),
            "j_above_min_phys": rpm_j_phys >= RPM_J_MIN,
            "p_above_min_phys": rpm_p_phys >= RPM_P_MIN,
            # Modo proporcional
            "rpm_j_prop"      : round(rpm_j_prop, 3),
            "rpm_p_prop"      : round(rpm_p_prop, 3),
            "active_mode"     : self.mode,
        }


# ── Test ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("COMPARATIVA MATLAB vs Python — Paciente 0 (74a, 65kg)")
    print("=" * 70)

    casos = [
        ("Inducción pico",       1.50,  5.80),
        ("Post-inducción",       0.40,  0.80),
        ("Mantenimiento típico", 0.05,  0.10),
        ("Dosis mínima",         0.01,  0.02),
    ]

    pump_prop = SerialPumpInterface(mode="proportional")
    pump_phys = SerialPumpInterface(mode="physical")

    print(f"\n{'Caso':<25} {'u_p(mg/s)':>10} {'u_r(μg/s)':>10} "
          f"{'RPM_J_phys':>12} {'RPM_P_phys':>12} "
          f"{'RPM_J_prop':>12} {'RPM_P_prop':>12}")
    print("-" * 95)

    for label, up, ur in casos:
        r = pump_prop.conversion_report(up, ur)
        mark_j = "✓" if r["j_above_min_phys"] else "✗STALL"
        mark_p = "✓" if r["p_above_min_phys"] else "✗STALL"
        print(f"{label:<25} {up:>10.3f} {ur:>10.3f} "
              f"{r['rpm_j_physical']:>10.2f}{mark_j:>4} "
              f"{r['rpm_p_physical']:>10.2f}{mark_p:>4} "
              f"{r['rpm_j_prop']:>12.2f} "
              f"{r['rpm_p_prop']:>12.2f}")

    print()
    print("Límites físicos:")
    print(f"  Jeringa    (propofol):    RPM ∈ [{RPM_J_MIN}, {RPM_J_MAX}]")
    print(f"  Peristáltica (remi):      RPM ∈ [{RPM_P_MIN}, {RPM_P_MAX}]")
    print()
    print("MATLAB App Designer para remi:")
    print("  sp_p = (u/0.0308)*(154-35)/217.27 + 35  → piso garantizado = 35 RPM")
    print()
    print("Modo 'proportional' (recomendado):")
    print("  Garantiza RPM_MIN en ambas bombas cuando u>0")
    print("  Propofol:  [0, 2.0 mg/s]  → [7.94, 20.1] RPM")
    print("  Remi:      [0, 7.0 μg/s]  → [33.2, 166]  RPM")
    print()
    print("Modo 'physical' (exacto pero jeringa se para en mantenimiento):")
    print("  Requiere diluir propofol a ~2 mg/mL para resolver hardware limit")