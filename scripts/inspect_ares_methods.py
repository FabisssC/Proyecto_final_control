from AReS.simulator import Simulator
from AReS.utils.enums import SimulatorMode

sim = Simulator.create(mode=SimulatorMode.INFUSION)

metodos = [m for m in dir(sim) if not m.startswith("_")]

for m in metodos:
    print(m)