from dataclasses import dataclass
from typing import Sequence

from AReS.simulator import Simulator
from AReS.utils.enums import SimulatorMode, DoHMeasure, Model, Interaction


@dataclass(frozen=True)
class AReSConfig:
    patient_id: int = 0
    t_s: int = 5
    doh_measure: DoHMeasure = DoHMeasure.BIS
    interaction: Interaction = Interaction.SURFACE
    pk_models: dict = None
    pd_models: dict = None

    def __post_init__(self):
        if self.t_s <= 0:
            raise ValueError("t_s debe ser mayor que 0.")

        if self.pk_models is None:
            object.__setattr__(self, "pk_models", {
                "prop": Model.ELEVELD,
                "remi": Model.ELEVELD,
                "nore": Model.JOACHIM,
                "rocu": Model.DAHE,
            })

        if self.pd_models is None:
            object.__setattr__(self, "pd_models", {
                "prop": Model.ELEVELD,
                "remi": Model.ELEVELD,
            })


class AReSInterface:
    def __init__(self, config: AReSConfig):
        self.config = config
        self.sim = None
        self.initialized = False

    def initialize(self, t_sim: int) -> None:
        if t_sim <= 0:
            raise ValueError("t_sim debe ser mayor que 0.")

        self.sim = Simulator.create(mode=SimulatorMode.INFUSION)

        self.sim.init_simulation_from_file(
            id_patient=self.config.patient_id,
            t_sim=t_sim,
            t_s=self.config.t_s,
            opiates=True,
            pk_models=self.config.pk_models,
            pd_models=self.config.pd_models,
            interaction=self.config.interaction,
            doh_measure=self.config.doh_measure,
            stimuli=None,
            volume_status=None,
            bring_to_maintenance=False,
        )

        self.initialized = True

    def run(
        self,
        u_prop: Sequence[float],
        u_remi: Sequence[float],
    ):
        if not self.initialized:
            raise RuntimeError("Primero debes llamar initialize().")

        if len(u_prop) != len(u_remi):
            raise ValueError("u_prop y u_remi deben tener la misma longitud.")

        n = len(u_prop)
        if n == 0:
            raise ValueError("Las entradas no pueden estar vacías.")

        u_nore = [0.0] * n
        u_rocu = [0.0] * n

        self.sim.run_complete_simulation(
            u_prop=list(u_prop),
            u_remi=list(u_remi),
            u_nore=u_nore,
            u_rocu=u_rocu,
        )

        self.sim.save_simulation()

        state = self.sim.get_patient_state_history()
        inputs = self.sim.get_patient_input_history()
        return state, inputs