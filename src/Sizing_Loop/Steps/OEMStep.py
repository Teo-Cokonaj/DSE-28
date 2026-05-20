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
from src.Structural_Weight_Penalties.fuselage_loading_model_cylinder import *

class OEMStep(DesignOptionStep):
    def __init__(self, resolution=1000, minimum_thickness=.001, print_:bool=False):
        self.resolution = resolution
        self.minimum_thickness = minimum_thickness
        self.print_ = print_

    def update(self, state:DesignOptionState) -> DesignOptionStateIterable:

        # COMPARATIVE PERFORMANCE AND BENEFIT ASSESSMENT OF
        # VTOL- AND CTOL-UAVS
        # D. F. Finger
        base_oem_fraction = 0.699*state.iterable.aircraft_parameters.total_mass**-.051

        delta_m = 0
        baseline_fuselage_mass = 0.

        if state.fixed.choices.canard_capability: #there is no case of movable port and no canard
            canard_lift_fraction = 0.

            W = state.iterable.aircraft_parameters.total_mass*CONSTANTS.G0

            #clean
            x, dx = x_range(fuselage_length = state.total_fuselage_length(), resolution = self.resolution)
            loads, title, L_main, L_empennage, L_canard = calculate_flight_case(x=x, W=W, canard_lift_fraction=canard_lift_fraction, main_wing_loc=state.x_c4_root_wing_from_nose(), empennage_loc=state.x_c4_tail_from_nose(), cg_loc=state.x_cg_from_nose(), canard_loc=0.).values()
            shear, moment = cumulative_shear_and_moment(dx=dx, loads=loads).values()
            t_skin_no_canard_static, critical_mode = thickness_for_combined_failure(shear=shear, moment=moment, x=x, yield_strength=CONSTANTS.YIELD_STRENGTH_CFRP, E = CONSTANTS.E_MODULUS_CFRP, fuselage_radius=state.fixed.assumptions.diameter_fuselage / 2, t_min=self.minimum_thickness)

            baseline_fuselage_mass = fuselage_skin_mass(x=x, dx=dx, t_skin=t_skin_no_canard_static, fuselage_radius=state.fixed.assumptions.diameter_fuselage / 2, material_density=CONSTANTS.DENSITY_CFRP)

            t_skin_no_canard_variable = t_skin_no_canard_static
            if state.fixed.choices.main_wing_x_movable:
                max_shear, max_moment = variable_port_iteration(x=x, wing_location=state.x_c4_root_wing_from_nose(), chord=state.iterable.lifting_surfaces[0].c_root, canard_lift_fraction=canard_lift_fraction, empennage_loc=state.total_fuselage_length(), cg_loc=state.x_cg_from_nose(), canard_loc=0., W=W, dx=dx)
                t_skin_no_canard_variable, critical_mode = thickness_for_combined_failure(shear=max_shear, moment=max_moment, x=x, yield_strength=CONSTANTS.YIELD_STRENGTH_CFRP, E = CONSTANTS.E_MODULUS_CFRP, fuselage_radius=state.fixed.assumptions.diameter_fuselage / 2, t_min=self.minimum_thickness)

            canard_lift_fraction = .2

            loads= calculate_flight_case(x=x, W=W, canard_lift_fraction=canard_lift_fraction, main_wing_loc=state.x_c4_root_wing_from_nose(), empennage_loc=state.x_c4_tail_from_nose(), cg_loc=state.x_cg_from_nose(), canard_loc=0.)["loads"]
            shear, moment = cumulative_shear_and_moment(dx=dx, loads=loads).values()

            fuselage_mass_canard_variable = 0.
            if state.fixed.choices.main_wing_x_movable:
                max_shear, max_moment = variable_port_iteration(x=x, wing_location=state.x_c4_root_wing_from_nose(), chord=state.iterable.lifting_surfaces[0].c_root, canard_lift_fraction=canard_lift_fraction, empennage_loc=state.total_fuselage_length(), cg_loc=state.x_cg_from_nose(), canard_loc=0., W=W, dx=dx)
                t_skin_canard_variable, critical_mode = thickness_for_combined_failure(shear=max_shear, moment=max_moment, x=x, yield_strength=CONSTANTS.YIELD_STRENGTH_CFRP, E = CONSTANTS.E_MODULUS_CFRP, fuselage_radius=state.fixed.assumptions.diameter_fuselage / 2, t_min=self.minimum_thickness)
                t_skin_fuselage = np.maximum(t_skin_no_canard_variable, t_skin_canard_variable)
                fuselage_mass_canard_variable = fuselage_skin_mass(x=x, dx=dx, t_skin=t_skin_fuselage, fuselage_radius=state.fixed.assumptions.diameter_fuselage / 2, material_density=CONSTANTS.DENSITY_CFRP)
                delta_m = fuselage_mass_canard_variable - baseline_fuselage_mass
                if self.print_:
                    print(f"{fuselage_mass_canard_variable} - {baseline_fuselage_mass} = {delta_m}")

            else:
                t_skin_canard_static, critical_mode = thickness_for_combined_failure(shear=shear, moment=moment, x=x, yield_strength=CONSTANTS.YIELD_STRENGTH_CFRP, E = CONSTANTS.E_MODULUS_CFRP, fuselage_radius=state.fixed.assumptions.diameter_fuselage / 2, t_min=self.minimum_thickness)
                t_skin_fuselage = np.maximum(t_skin_no_canard_static, t_skin_canard_static)
                fuselage_mass_canard_static = fuselage_skin_mass(x=x, dx=dx, t_skin=t_skin_fuselage, fuselage_radius=state.fixed.assumptions.diameter_fuselage / 2, material_density=CONSTANTS.DENSITY_CFRP)
                delta_m = fuselage_mass_canard_static - baseline_fuselage_mass
                if self.print_:
                    print(f"{fuselage_mass_canard_static} - {baseline_fuselage_mass} = {delta_m}")

        state.iterable.aircraft_parameters.empty_mass_fraction = base_oem_fraction + delta_m / state.iterable.aircraft_parameters.total_mass
        return state.iterable
