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
from src.LandingGear.landingGearLength import lg_pos_and_length
from src.objects.lading_gear import LandingGear
from src.global_parameters import CONSTANTS

class LandingGearStep(DesignOptionStep):
    def update(self, state:DesignOptionState) -> DesignOptionStateIterable:

        l_opt, x_mlg_opt, Y_lg_opt, x_nlg_opt = lg_pos_and_length(
            L1=state.fixed.assumptions.fuselage_length1_per_area * state.iterable.lifting_surfaces[0].wing_area,
            L2=state.fixed.assumptions.fuselage_length2_per_area * state.iterable.lifting_surfaces[0].wing_area,
            L3=state.fixed.assumptions.fuselage_length3_per_area * state.iterable.lifting_surfaces[0].wing_area,
            x_cg=state.x_cg_from_nose(),
            up_sweep_angle=state.fixed.assumptions.fuselage_upsweep,
            diameter_fuselage=state.fixed.assumptions.diameter_fuselage
        )

        state.iterable.landing_gear = LandingGear(x_mlg_opt, x_nlg_opt, l_opt, Y_lg_opt)
        return state.iterable
