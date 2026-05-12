import aerosandbox as asb
import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import os
import sys

current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.append(project_root)

from src.Sizing_Loop.DesignOptionStep import DesignOptionStep
from src.Sizing_Loop.DesignOptionStateIterable import DesignOptionStateIterable
from src.Class_I.Class_I import Class_I, Class_I_Result
from src.global_parameters import CONSTANTS

class WeightEstimationStep(DesignOptionStep):
    def __init__(self, debug=False):
        self.debug = debug


    def update(self, state) -> DesignOptionStateIterable:

        class_I = Class_I(
            altitude_cruise=state.fixed.assumptions.ALTITUDE_CRUISE,
            altitude_go_around=state.fixed.assumptions.ALTITUDE_GO_AROUND,
            efficiency_engine_total=state.iterable.propulsion_parameters.engine_parameters.efficiency_total,
            energy_density_saf=state.fixed.assumptions.energy_density_saf,
            time_half_turn=state.fixed.assumptions.TIME_HALF_CIRCLE,
            debug=self.debug
        )

        class_I_result = class_I.run_estimation(
            oem_fraction=state.iterable.aircraft_parameters.empty_mass_fraction,
            CL_max_glide_ratio_go_around=np.sqrt(state.iterable.performance_parameters.go_around_parameters.CD0 
                                        * state.iterable.performance_parameters.go_around_parameters.inviscid_ratio),
            glide_ratio_mach_max=.5 * np.sqrt(state.iterable.performance_parameters.mach_max_parameters.inviscid_ratio 
                                        / state.iterable.performance_parameters.mach_max_parameters.CD0),
            glide_ratio_cruise=.5 * np.sqrt(state.iterable.performance_parameters.cruise_parameters.inviscid_ratio 
                                        / state.iterable.performance_parameters.cruise_parameters.CD0),
            glide_ratio_go_around=.5 * np.sqrt(state.iterable.performance_parameters.go_around_parameters.inviscid_ratio 
                                        / state.iterable.performance_parameters.go_around_parameters.CD0),
            airspeed_approach=np.sqrt(state.fixed.assumptions.airfield_length/.6),
            wing_loading=CONSTANTS.G0 * state.iterable.aircraft_parameters.total_mass
                         / state.iterable.lifting_surfaces[0].wing_area
        )

        state.iterable.aircraft_parameters.fuel_mass_fraction = class_I_result.fuel_fraction
        state.iterable.aircraft_parameters.total_mass = class_I_result.mtom

        return state.iterable

