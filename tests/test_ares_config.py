from AReS.utils.enums import Interaction
from control_anestesia.simulator_interface.ares_interface import AReSConfig


def test_default_config_sets_surface_interaction():
    cfg = AReSConfig()
    assert cfg.interaction == Interaction.SURFACE
