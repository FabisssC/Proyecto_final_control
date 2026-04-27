import inspect

from AReS.simulator import Simulator
from AReS.utils.enums import SimulatorMode

sim = Simulator.create(mode=SimulatorMode.INFUSION)

print(inspect.signature(sim.one_step_simulation))
print(inspect.getsource(sim.one_step_simulation))