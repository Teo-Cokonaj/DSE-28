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

        atmosphere_cruise = asb.Atmosphere(state.fixed.assumptions.ALTITUDE_CRUISE)
        atmosphere_go_around = asb.Atmosphere(state.fixed.assumptions.ALTITUDE_GO_AROUND)
        atmosphere_mach_max = asb.Atmosphere(CONSTANTS.ALTITUDE_MACH_MAX)

        sfc = state.iterable.propulsion_parameters.engine_parameters.sfc
        ef = state.fixed.assumptions.energy_density_saf

        efficiency_cruise = CONSTANTS.MACH_CRUISE * atmosphere_cruise.speed_of_sound() / sfc / ef
        efficiency_go_around = state.mach_go_around() * atmosphere_go_around.speed_of_sound() / sfc / ef 
        efficiency_mach_max = CONSTANTS.MACH_MAX * atmosphere_mach_max.speed_of_sound() /sfc / ef

        if self.debug:
            print()
            print("Efficiencies:")
            print(efficiency_cruise)
            print(efficiency_go_around)
            print(efficiency_mach_max)

        class_I = Class_I(
            altitude_cruise=state.fixed.assumptions.ALTITUDE_CRUISE,
            altitude_go_around=state.fixed.assumptions.ALTITUDE_GO_AROUND,
            efficiency_engine_cruise=efficiency_cruise,
            energy_density_saf=state.fixed.assumptions.energy_density_saf,
            time_half_turn=state.fixed.assumptions.TIME_HALF_CIRCLE,
            debug=self.debug,
            efficiency_engine_mach_max=efficiency_mach_max,
            efficiency_engine_go_around=efficiency_go_around
        )

        #NOTE: for cruise and mach max, we need to fly at a particular speed so we don NOT fly at the optimal glide ratio!
        class_I_result = class_I.run_estimation(
            oem_fraction=state.iterable.aircraft_parameters.empty_mass_fraction,
            CL_max_glide_ratio_go_around=state.iterable.performance_parameters.go_around_parameters.CL_range_jet_max(),
            glide_ratio_mach_max=state.glide_ratio_mach_max(),
            glide_ratio_cruise=state.glide_ratio_cruise(),
            glide_ratio_go_around=state.iterable.performance_parameters.go_around_parameters.glide_ratio_range_jet_max(),
            airspeed_approach=state.fixed.assumptions.airspeed_approach,
            wing_loading=state.wing_loading()
        )

        state.iterable.aircraft_parameters.fuel_mass_fraction = class_I_result.fuel_fraction
        state.iterable.aircraft_parameters.total_mass = class_I_result.mtom

        return state.iterable

