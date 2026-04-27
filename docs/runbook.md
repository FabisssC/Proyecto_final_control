# Runbook operativo

## Proposito

Este documento resume los pasos operativos para reconstruir el entorno, ejecutar los experimentos principales y recordar la organizacion actual del proyecto. La descripcion arquitectonica detallada, junto con los diagramas de flujo de datos y la trazabilidad de senales, se encuentra en [README.md](</C:/Users/casti/OneDrive - Instituto Politecnico Nacional/OCTAVO SEMESTRE/P.I/PTIII/simulaciones_trabajo_final/Proyecto_control_py_AReS/README.md>).

## Preparacion del entorno

La preparacion recomendada es:

```bash
conda env create -f environment.yml
conda activate control_anestesia_env
pip install -e .
```

Si `AReS` no queda resuelto automaticamente desde el archivo de entorno, instalarlo manualmente:

```bash
pip install -e ../AReS-Anesthesia-Response-Simulator/python
```

Supuesto operativo actual:

- el repositorio externo `AReS-Anesthesia-Response-Simulator` existe como carpeta hermana del presente repositorio

## Experimentos principales

### 1. Simulacion de referencia en lazo abierto

```bash
python scripts/run_baseline.py
```

Este experimento valida la encapsulacion de `AReS` como planta y la organizacion de resultados en `DataFrame`.

### 2. Lazo cerrado con PID y ratio fijo

```bash
python scripts/run_pid_ratio.py
```

Este experimento evalua el control de `BIS` sin observadores ni logica de deteccion.

### 3. Lazo cerrado con observador por intervalo y deteccion

```bash
python scripts/run_pid_observer.py
```

Este experimento activa la cadena completa:

- control PID
- separacion entre `u_cmd` y `u_app`
- simulacion paso a paso con `AReS`
- observadores por intervalo
- reconstruccion de `Ce_bis` y de bandas de `BIS`
- deteccion de fallas de actuacion

## Parametros relevantes del experimento con observador

El escenario principal se implementa en [src/control_anestesia/scenarios/closed_loop_pid_observer.py](</C:/Users/casti/OneDrive - Instituto Politecnico Nacional/OCTAVO SEMESTRE/P.I/PTIII/simulaciones_trabajo_final/Proyecto_control_py_AReS/src/control_anestesia/scenarios/closed_loop_pid_observer.py:58>). Los parametros nominales que conviene recordar son:

- `Ts_s = 5`
- `duracion_min = 60`
- `BIS_ref = 50.0`
- `ratio = 2.0`
- saturacion de `u_prop` entre `0.0` y `10.0`
- saturacion de `u_remi` entre `0.0` y `20.0`

## Inyeccion de fallas

Las fallas de actuacion se modelan en [src/control_anestesia/fault_detection/fault_scenarios.py](</C:/Users/casti/OneDrive - Instituto Politecnico Nacional/OCTAVO SEMESTRE/P.I/PTIII/simulaciones_trabajo_final/Proyecto_control_py_AReS/src/control_anestesia/fault_detection/fault_scenarios.py:1>). La idea operativa es:

- `u_cmd` representa la senal calculada por el controlador
- `u_app` representa la senal realmente aplicada a la planta
- una falla de bomba queda representada por una discrepancia `u_app != u_cmd`

Escenarios ya contemplados:

- perdida parcial de efectividad con `factor < 1`
- fallo total con `factor = 0`

## Estimulos fisiologicos

Existe soporte para estimulos fisiologicos a traves del argumento `stimuli` en [src/control_anestesia/simulator_interface/ares_step_interface.py](</C:/Users/casti/OneDrive - Instituto Politecnico Nacional/OCTAVO SEMESTRE/P.I/PTIII/simulaciones_trabajo_final/Proyecto_control_py_AReS/src/control_anestesia/simulator_interface/ares_step_interface.py:16>). Un ejemplo de configuracion se encuentra en [scripts/run_pid_observer.py](</C:/Users/casti/OneDrive - Instituto Politecnico Nacional/OCTAVO SEMESTRE/P.I/PTIII/simulaciones_trabajo_final/Proyecto_control_py_AReS/scripts/run_pid_observer.py:7>).

Uso metodologico:

- validar que el detector no confunda perturbaciones fisiologicas con fallas de actuacion

## Artefactos a revisar tras una corrida

Despues de ejecutar `scripts/run_pid_observer.py`, las variables de interes para inspeccion son:

- `BIS`, `BIS_ref`, `BIS_mas`, `BIS_menos`
- `Ce_prop`, `Ce_prop_mas`, `Ce_prop_menos`
- `Ce_remi`, `Ce_remi_mas`, `Ce_remi_menos`
- `Ce_bis`, `Ce_bis_mas`, `Ce_bis_menos`
- `r_prop_sup`, `r_prop_inf`, `r_remi_sup`, `r_remi_inf`
- `fallo_prop`, `fallo_remi`
- `u_prop_cmd`, `u_prop_app`, `u_remi_cmd`, `u_remi_app`

## Proximos pasos recomendados

Para mantener la trazabilidad del proyecto conforme siga creciendo, la siguiente secuencia es razonable:

1. mover parametros nominales del escenario con observador a archivos de configuracion
2. registrar escenarios de falla y de estimulos en configuraciones versionadas
3. agregar pruebas unitarias para observador, filtro BIS y detector
4. consolidar exportacion de resultados a `csv` para comparaciones entre corridas
