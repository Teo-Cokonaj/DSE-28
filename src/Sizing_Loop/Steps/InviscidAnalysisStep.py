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
from src.aerodynamic_model.lifting_line_theory import LiftingLineTheory
from src.global_parameters import CONSTANTS

class InviscidAnalysisStep(DesignOptionStep):
    def __init__(self, plot=False, debug=False):
        self.plot = plot
        self.debug = debug

    def update(self, state) -> DesignOptionStateIterable:
        lifting_line_model = LiftingLineTheory(
            aircraft_parameters=state.iterable.aircraft_parameters,
            wing_planform=state.iterable.lifting_surfaces[0],
            horizontal_stabilizer_planform=state.iterable.lifting_surfaces[1],
            vertical_stabilizer_planform=state.iterable.lifting_surfaces[2]
        )

        lifting_line_model.initialize_airfoils()
        lifting_line_model.make_full_airplane_model(main_wing=True, horizontal_stabilizer=True, vertical_stabilizer=True)

        if self.plot:
            lifting_line_model.airplane.draw()

        approach_mach = state.fixed.assumptions.airspeed_approach / asb.Atmosphere().speed_of_sound()
        state.iterable.performance_parameters.climb_OEI_parameters.inviscid_ratio = self._exctract_inviscid_ratio_for_condition(lifting_line_model, approach_mach, CONSTANTS.ALTITUDE_OEI_CLIMB)
        state.iterable.performance_parameters.takeoff_parameters.inviscid_ratio = self._exctract_inviscid_ratio_for_condition(lifting_line_model, approach_mach, 0.)
        state.iterable.performance_parameters.go_around_parameters.inviscid_ratio = self._exctract_inviscid_ratio_for_condition(lifting_line_model, state.mach_go_around(), state.fixed.assumptions.ALTITUDE_GO_AROUND)
        state.iterable.performance_parameters.cruise_parameters.inviscid_ratio = self._exctract_inviscid_ratio_for_condition(lifting_line_model, CONSTANTS.MACH_CRUISE, state.fixed.assumptions.ALTITUDE_CRUISE)
        state.iterable.performance_parameters.mach_max_parameters.inviscid_ratio = self._exctract_inviscid_ratio_for_condition(lifting_line_model, CONSTANTS.MACH_MAX, CONSTANTS.ALTITUDE_MACH_MAX) 

        return state.iterable       
    

    def _exctract_inviscid_ratio_for_condition(self, lifting_line_model:LiftingLineTheory, mach:float, altitude:float):
        atmosphere = asb.Atmosphere(altitude)
        velocity = mach * atmosphere.speed_of_sound()

        #alpha_analysis = lifting_line_model.find_aoa_for_force_equilibrium(velocity=velocity, altitude_m=altitude)

        if self.debug:
            inviscid_ratios = list()
            for alpha_analysis in np.linspace(1., 10., 11): #NOTE: breaks at the AOA of zero
                _, results = lifting_line_model.run_llt_arbitrary_analysis(
                    velocity=velocity, 
                    altitude_m=altitude, 
                    angle_of_attack_deg=alpha_analysis
                )
                inviscid_ratios.append(lifting_line_model.extract_L2_Di_ratio(results))

            print(f"STD: {np.std(inviscid_ratios)}, all: {inviscid_ratios}")
            return np.average(inviscid_ratios)
        
        else:
            _, results = lifting_line_model.run_llt_arbitrary_analysis(
                    velocity=velocity, 
                    altitude_m=altitude, 
                    angle_of_attack_deg=5. #NOTE: verified that the AoA does not influence the inviscid ratio
                )

            return lifting_line_model.extract_L2_Di_ratio(results)


        