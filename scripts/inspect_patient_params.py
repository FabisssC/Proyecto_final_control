# scripts/inspect_patient_params.py
from AReS.simulator import Simulator
from AReS.utils.enums import SimulatorMode, Model, Interaction, DoHMeasure

sim = Simulator.create(mode=SimulatorMode.INFUSION)
sim.init_simulation_from_file(
    id_patient=0,
    t_sim=10,
    t_s=5,
    opiates=True,
    pk_models={"prop": Model.ELEVELD, "remi": Model.ELEVELD,
               "nore": Model.JOACHIM, "rocu": Model.DAHE},
    pd_models={"prop": Model.ELEVELD, "remi": Model.ELEVELD},
    interaction=Interaction.SURFACE,
    doh_measure=DoHMeasure.BIS,
    stimuli=None,
    volume_status=None,
    bring_to_maintenance=False,
)

# Intentar los métodos más comunes para demografía
for method in ["get_patient_demographics", "get_patient_info",
               "get_patient_state", "patient"]:
    if hasattr(sim, method):
        print(f"\n--- {method}() ---")
        try:
            result = getattr(sim, method)()
            print(result)
        except Exception as e:
            print(f"Error: {e}")

# También buscar atributos directos
for attr in dir(sim):
    if any(k in attr.lower() for k in ["age", "weight", "height", "patient"]):
        print(f"Atributo: {attr} = {getattr(sim, attr, '?')}")