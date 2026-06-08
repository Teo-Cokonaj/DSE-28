import sys
import os
import pytest
import numpy as np
import copy

current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.append(project_root)

from src.Sizing_Loop.Steps.LandingGearStep import LandingGearStep
from src.Sizing_Loop.DesignOptionState import DesignOptionState
from src.aerodynamic_model.lifting_line_inviscid import LiftingLineInviscid
from src.Sizing_Loop.DesignOptionStateIterable import DesignOptionStateIterable
from src.airfoil.SymmetricAirfoil import SymmetricAirfoil
from src.global_parameters import CONSTANTS

from src.objects.aircraft_parameters import AircraftParameters
from src.objects.lading_gear import LandingGear
from src.objects.lifting_surface_planform import LiftingSurfacePlanform
from src.objects.performance_parameters import PerformanceParameters, PerformanceAtAltitude
from src.objects.propulsion_parameters import PropulsionParameters, EngineParameters

def initial_state_interior() -> DesignOptionState:
    return DesignOptionState(
        DesignOptionStateIterable(
            aircraft_parameters=AircraftParameters(
                total_mass=50.,
                #NOTE: large distance to prevent interference
                horizontal_stabilizer_distance_from_wing=10.,
                vertical_stabilizer_distance_from_wing=10.,
                canard_distance_in_front_of_wing=0.,
                z_horizontal_stabiliser=1.
            ),
            lifting_surfaces=[
                LiftingSurfacePlanform(
                    aspect_ratio=6.,
                    span=2, # [m]
                    sweep_quarter_deg=0., # [m]
                    taper=1.,
                    tip_twist_rad=0.,
                ),
                LiftingSurfacePlanform(
                    aspect_ratio=6.,
                    span=2., # [m]
                    sweep_quarter_deg=0., # [m]
                    taper=1.,
                    tip_twist_rad=0.,
                ),
                LiftingSurfacePlanform(
                    aspect_ratio=2,
                    span=.5, # [m]
                    sweep_quarter_deg=25., # [m]
                    taper=1.,
                    tip_twist_rad=0.,
                )
            ],
            propulsion_parameters=PropulsionParameters(EngineParameters(250., .1, .5, .15), 2),
            landing_gear=LandingGear(2., .5, .15, .1),
            performance_parameters=PerformanceParameters(
                cruise_parameters=PerformanceAtAltitude(np.pi*.8*20., .01),
                mach_max_parameters=PerformanceAtAltitude(np.pi*.75*20., .02),
                go_around_parameters=PerformanceAtAltitude(np.pi*.9*20., .015),
                takeoff_parameters=PerformanceAtAltitude(np.pi*.9*20., .025),
                climb_OEI_parameters=PerformanceAtAltitude(np.pi*.87*20., .023)
            )
        )
    )


@pytest.fixture
def initial_state() -> DesignOptionState:
    return initial_state_interior()


class TestLandingGearStep():
    def test_update(self, initial_state:DesignOptionState, print_=False):
        lg_step = LandingGearStep(print_)
        initial_state.fixed.choices.wing_interference_factor = 1.2
        if print_:
            print(initial_state.fixed.assumptions.fuselage_length1 + initial_state.fixed.assumptions.fuselage_length2)

        for x_cg_per_mac in np.linspace(0., 0.9, 5):
            modified_state = copy.deepcopy(initial_state)
            modified_state.iterable.aircraft_parameters.x_cg_per_mac = x_cg_per_mac
            new_lg = lg_step.update(modified_state).landing_gear

            if print_:
                print()
                print(x_cg_per_mac)
                print(modified_state.total_fuselage_length())
                print(modified_state.x_cg_from_nose())
                print(new_lg.length_z, new_lg.y_main_lg, new_lg.x_main_lg, new_lg.x_nose_lg, new_lg.length_pythagorean())
                print(new_lg.length_z / new_lg.length_pythagorean())
            
            assert new_lg.length_z < modified_state.fixed.assumptions.diameter_fuselage, modified_state.fixed.assumptions.diameter_fuselage

            alpha = np.arctan(new_lg.y_main_lg / (new_lg.x_main_lg - new_lg.x_nose_lg))
            c = (modified_state.x_cg_from_nose() - new_lg.x_nose_lg) * np.sin(alpha)
            psi = np.arctan(new_lg.length_z / c)
            if print_:
                print(np.rad2deg(psi))
            assert  psi < 55*np.pi / 180 + 0.001


if __name__ == "__main__":
    tlg = TestLandingGearStep()
    tlg.test_update(initial_state_interior(), True)