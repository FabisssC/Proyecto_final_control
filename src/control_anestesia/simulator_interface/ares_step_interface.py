import numpy as np
import pandas as pd

from control_anestesia.simulator_interface.ares_interface import AReSConfig
from AReS.simulator import Simulator
from AReS.utils.enums import SimulatorMode
from AReS.utils.enums import DisturbanceType


class AReSStepInterface:
    def __init__(self, config: AReSConfig):
        self.config = config
        self.sim = None
        self.initialized = False

    def initialize(self, t_sim: int, stimuli=None):
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
            stimuli=stimuli,
            volume_status=None,
            bring_to_maintenance=False,
        )

        self.initialized = True

    def step(self, u_prop, u_remi):
        self.sim.one_step_simulation(
            u_prop=float(u_prop),
            u_remi=float(u_remi),
            u_nore=0.0,
            u_rocu=0.0
        )

        state = self.sim.get_patient_state()
        return state

    def get_history(self):
        state = self.sim.get_patient_state_history()
        inputs = self.sim.get_patient_input_history()

        return state, inputs