import aerosandbox as asb
import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import os
import sys

current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.append(project_root)

from src.Sizing_Loop.DesignOptionStep import DesignOptionStep
from src.Sizing_Loop.DesignOptionState import DesignOptionState
from src.Sizing_Loop.DesignOptionStateIterable import DesignOptionStateIterable
from src.MatchingDiagram.MatchingDiagramJet import MatchingDiagramJet
from src.global_parameters import CONSTANTS

class OEMStep(DesignOptionStep):
    def update(self, state:DesignOptionState) -> DesignOptionStateIterable:

        # COMPARATIVE PERFORMANCE AND BENEFIT ASSESSMENT OF
        # VTOL- AND CTOL-UAVS
        # D. F. Finger
        base_oem_fraction = 0.699*state.iterable.aircraft_parameters.total_mass**-.051

        delta_m = 0

        if state.fixed.choices.canard_capability:
            delta_m += 1. #TODO: add additional mass from canard

        if state.fixed.choices.main_wing_x_movable:
            delta_m += 1.5 #TODO: add main wing movable

        state.iterable.aircraft_parameters.empty_mass_fraction = base_oem_fraction + delta_m / state.iterable.aircraft_parameters.total_mass
        return state.iterable
