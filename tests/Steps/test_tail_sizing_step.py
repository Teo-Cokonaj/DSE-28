import copy
import pytest
import sys
import os
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.aerodynamic_model.lifting_line_theory import LiftingLineTheory
from src.objects.lifting_surface_planform import LiftingSurfacePlanform
from src.tail_sizing.tail_sizing import TailVolume
from src.Sizing_Loop.Steps.tail_sizing_step import TailSizingStep
from src.Sizing_Loop.DesignOptionState import DesignOptionState
from src.Sizing_Loop.DesignOptionStateIterable import DesignOptionStateIterable
from src.Sizing_Loop.DesignOptionStateFixed import DesignOptionStateFixed
from src.Sizing_Loop.DesignOptionChoices import DesignOptionChoices
from src.objects.aircraft_parameters import AircraftParameters
from src.objects.performance_parameters import PerformanceParameters, PerformanceAtAltitude
from src.objects.possible_engines import PossibleEngines
from src.objects.lading_gear import LandingGear
from src.global_parameters import CONSTANTS, Assumptions


@pytest.fixture
def constants():
    return CONSTANTS()


@pytest.fixture
def assumptions():
    return Assumptions()

@pytest.fixture
def aircraft_parameters():
    return AircraftParameters(total_mass=50.0,
                        horizontal_stabilizer_distance_from_wing=3.0,
                        vertical_stabilizer_distance_from_wing=3.0,
                        canard_distance_in_front_of_wing=0.5)

@pytest.fixture
def wing_planform():
    return LiftingSurfacePlanform(aspect_ratio=25.0,
                                span=2.0,
                                sweep_quarter_deg=30.0,
                                taper=1.0,
                                tip_twist_rad=0.0)

@pytest.fixture
def horizontal_stabilizer_planform():
     return LiftingSurfacePlanform(aspect_ratio=3.0,
                                                                span=0.5,
                                                                sweep_quarter_deg=30.0,
                                                                taper=1.0,
                                                                tip_twist_rad=0.0)

@pytest.fixture
def vertical_stabilizer_planform():
     return LiftingSurfacePlanform(aspect_ratio=3.0,
                                                                span=0.3,
                                                                sweep_quarter_deg=0.0,
                                                                taper=0.3,
                                                                tip_twist_rad=0.0)

@pytest.fixture
def canard_planform():
     return LiftingSurfacePlanform(aspect_ratio=3.0,
                                                                span=0.3,
                                                                sweep_quarter_deg=45.0,
                                                                taper=1.0,
                                                                tip_twist_rad=0.0)

@pytest.fixture
def lifting_line_theory(aircraft_parameters,
                        wing_planform,
                        horizontal_stabilizer_planform,
                        vertical_stabilizer_planform):

     return LiftingLineTheory(aircraft_parameters,
                            wing_planform,
                            horizontal_stabilizer_planform,
                            vertical_stabilizer_planform,
                                          )


@pytest.fixture
def tail_sizing_step():
    return TailSizingStep(number_of_sections_wing=100,
                          number_of_sections_others=5)

@pytest.fixture
def design_option_iterable(aircraft_parameters,
                           wing_planform,
                           horizontal_stabilizer_planform,
                           vertical_stabilizer_planform,
                           canard_planform):
    return DesignOptionStateIterable(
            aircraft_parameters,
            lifting_surfaces=[
                wing_planform,
                horizontal_stabilizer_planform,
                vertical_stabilizer_planform,
                canard_planform
            ],
            propulsion_parameters=PossibleEngines().engineTJ40_G1,

            #insignificant - will get overwritten before it influences anything
            landing_gear=LandingGear(2., .5, .15, .1),
            performance_parameters=PerformanceParameters(
                cruise_parameters=PerformanceAtAltitude(np.pi*.8*20., .01),
                mach_max_parameters=PerformanceAtAltitude(np.pi*.75*20., .02),
                go_around_parameters=PerformanceAtAltitude(np.pi*.9*20., .015),
                takeoff_parameters=PerformanceAtAltitude(np.pi*.9*20., .025),
                climb_OEI_parameters=PerformanceAtAltitude(np.pi*.87*20., .023)
            )
        )

@pytest.fixture
def configuration():
    return DesignOptionChoices(
                name="HUG-CFG-302",
                canard_capability=False,
                landing_gear_sideways_extendable=False,
                wing_interference_factor=1.0,
                main_wing_x_movable=False
            )

@pytest.fixture
def design_option_fixed(assumptions,
                        configuration):
    return DesignOptionStateFixed(
                        assumptions,
                        configuration
                    )

@pytest.fixture
def design_option_state(design_option_iterable,
                        design_option_fixed):
    return DesignOptionState(
                    iterable=copy.deepcopy(design_option_iterable), 
                    _fixed=design_option_fixed
    )


class TestTailSizingStep:
    # @pytest.mark.dependency(depends=["test_tail_volume.py::test_required_tail_volume"], scope="session")
    # @pytest.mark.dependency(depends=["test_tail_volume.py::test_required_cg_position"], scope="session")
    def test_update(self,
                    tail_sizing_step,
                    design_option_state,
                    lifting_line_theory):
        
        original_state = copy.deepcopy(design_option_state)
        original_state.wing_downwash_gradient=0.0
        original_state.approach_speed = design_option_state.fixed.assumptions.airspeed_approach
        self.horizontal_stabilizer_arm = design_option_state.fixed.assumptions.moment_arm_per_area*design_option_state.iterable.lifting_surfaces[0].wing_area

        numerical_results = tail_sizing_step.update(design_option_state)
        computed_new_wing_area=numerical_results.lifting_surfaces[1].wing_area
        computed_new_x_cg_per_mac=numerical_results.aircraft_parameters.x_cg_per_mac

        lifting_line_theory.wing_number_of_sections =100
        lifting_line_theory.canard_number_of_sections = 5
        lifting_line_theory.horizontal_stabilizer_number_of_sections = 5
        lifting_line_theory.vertical_stabilizer_number_of_sections =5
        lifting_line_theory.initialize_airfoils()
        #Aircraft without tail
        lifting_line_theory.make_full_airplane_model(main_wing=True,
                                                      canard=False,
                                                      horizontal_stabilizer=False,
                                                      vertical_stabilizer=False)
        A_minus_H_results = lifting_line_theory.run_llt_alpha_sweep(velocity=original_state.approach_speed,
                                                                                 altitude_m=original_state.fixed.assumptions.ALTITUDE_CRUISE)
        ac_position_MAC = A_minus_H_results["x_ac"]/original_state.iterable.lifting_surfaces[0].MAC
        C_L_alpha_A_minus_H = A_minus_H_results["lift_curve_slope_per_rad"]
        Cmac = A_minus_H_results["Cmac"]
        #Only tail
        lifting_line_theory.make_full_airplane_model(main_wing=False,
                                                      canard=False,
                                                      horizontal_stabilizer=True,
                                                      vertical_stabilizer=True)

        H_results = lifting_line_theory.run_llt_alpha_sweep(velocity=original_state.approach_speed,
                                                            altitude_m=original_state.fixed.assumptions.ALTITUDE_CRUISE)
        C_L_alpha_H = H_results["lift_curve_slope_per_rad"]

        tail_volume = TailVolume(wing_planform=original_state.iterable.lifting_surfaces[0],
                            required_cg_excursion_MAC=original_state.fixed.assumptions.CG_EXCURSION_MAC,
                            ac_position_mac=ac_position_MAC,
                            C_L_H=original_state.CL_h_max(),
                            C_L_A_minus_H=original_state.CL_A_h(),
                            wing_downwash_gradient=original_state.wing_downwash_gradient,
                            C_L_alpha_A_minus_H = C_L_alpha_A_minus_H,
                            Cmac=Cmac,
                            C_L_alpha_H=C_L_alpha_H,
                            )
        
        tail_volume.find_required_tail_volume()
        reference_new_wing_area=tail_volume.required_tail_volume/original_state.iterable.aircraft_parameters.horizontal_stabilizer_distance_from_wing
        tail_volume.find_required_cg_position_MAC()
        reference_new_x_cg_per_mac = tail_volume.required_CG_position_MAC

        assert np.isclose(reference_new_wing_area,computed_new_wing_area)
        assert np.isclose(reference_new_x_cg_per_mac,computed_new_x_cg_per_mac)