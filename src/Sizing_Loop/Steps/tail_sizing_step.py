import aerosandbox as asb
import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import os
import sys

current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.append(project_root)

from src.objects.aircraft_parameters import AircraftParameters
from src.Sizing_Loop.DesignOptionStep import DesignOptionStep
from src.Sizing_Loop.DesignOptionStateIterable import DesignOptionStateIterable
from src.tail_sizing.tail_sizing import TailVolume
from src.aerodynamic_model.lifting_line_theory import LiftingLineTheory
from src.global_parameters import CONSTANTS

class TailSizingStep(DesignOptionStep):
    def __init__(self, debug=False):
        self.debug = debug


    def update(self, state) -> DesignOptionStateIterable:

        self.wing_downwash_gradient=0.0
        self.approach_speed = state.fixed.assumptions.airspeed_approach
        self.horizontal_stabilizer_arm = state.fixed.assumptions.moment_arm_per_area*state.iterable.lifting_surfaces[0].wing_area

        aircraft_parameters=AircraftParameters(total_mass=state.iterable.aircraft_parameters.total_mass,
                 horizontal_stabilizer_distance_from_wing=self.horizontal_stabilizer_arm,
                 vertical_stabilizer_distance_from_wing=self.horizontal_stabilizer_arm,
                 canard_distance_in_front_of_wing=state.iterable.aircraft_parameters.canard_distance_in_front_of_wing,
                 x_cg_per_mac=state.iterable.aircraft_parameters.x_cg_per_mac,
                 )

        lifting_line_theory = LiftingLineTheory(aircraft_parameters=aircraft_parameters,
                                                wing_planform=state.iterable.lifting_surfaces[0],
                                                horizontal_stabilizer_planform=state.iterable.lifting_surfaces[1],
<<<<<<< HEAD
                                                vertical_stabilizer_planform=state.iterable.lifting_surfaces[2],
                                                )
=======
                                                vertical_stabilizer_planform=state.iterable.lifting_surfaces[2],)
                                                #canard_planform=state.iterable.lifting_surfaces[3])
>>>>>>> 1429e546ffb9bdf3abe91ff91f2ce3ce1bee439c
        lifting_line_theory.initialize_airfoils()

        #Aircraft without tail
        lifting_line_theory.make_full_airplane_model(main_wing=True,
                                                      canard=False,
                                                      horizontal_stabilizer=False,
                                                      vertical_stabilizer=False)

        A_minus_H_results = lifting_line_theory.run_llt_alpha_sweep(velocity=self.approach_speed,
                                                                                 altitude_m=state.fixed.assumptions.ALTITUDE_CRUISE)
        self.ac_position_MAC = A_minus_H_results["x_ac"]/state.iterable.lifting_surfaces[0].MAC
        self.C_L_alpha_A_minus_H = A_minus_H_results["lift_curve_slope_per_rad"]
        self.Cmac = A_minus_H_results["Cmac"]

        #Only tail
        lifting_line_theory.make_full_airplane_model(main_wing=False,
                                                      canard=False,
                                                      horizontal_stabilizer=True,
                                                      vertical_stabilizer=True)

        H_results = lifting_line_theory.run_llt_alpha_sweep(velocity=self.approach_speed,
                                                            altitude_m=state.fixed.assumptions.ALTITUDE_CRUISE)
        self.C_L_alpha_H = H_results["lift_curve_slope_per_rad"]

        tail_volume = TailVolume(wing_planform=state.iterable.lifting_surfaces[0],
                            required_cg_excursion_MAC=state.fixed.assumptions.CG_EXCURSION_MAC,
                            ac_position_mac=self.ac_position_MAC,
                            C_L_H=state.CL_h_max(),
                            C_L_A_minus_H=state.CL_A_h(),
                            wing_downwash_gradient=self.wing_downwash_gradient,
                            C_L_alpha_A_minus_H = self.C_L_alpha_A_minus_H,
                            Cmac=self.Cmac,
                            C_L_alpha_H=self.C_L_alpha_H,
                            )
        
        tail_volume.find_required_tail_volume()
        state.iterable.lifting_surfaces[1].wing_area=tail_volume.required_tail_volume/state.iterable.aircraft_parameters.horizontal_stabilizer_distance_from_wing
        tail_volume.find_required_cg_position_MAC()
        state.iterable.aircraft_parameters.x_cg_per_mac = tail_volume.required_CG_position_MAC

        return state.iterable