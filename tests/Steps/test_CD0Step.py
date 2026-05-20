import aerosandbox as asb
import aerosandbox.numpy as np
from copy import deepcopy
import os
import sys
import pytest

current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.append(project_root)

from src.Sizing_Loop.Steps.CD0Step import CD0Step
from src.objects.possible_engines import PossibleEngines
from src.Sizing_Loop.DesignOptionState import DesignOptionState
from src.Sizing_Loop.DesignOptionStateIterable import DesignOptionStateIterable
from src.global_parameters import CONSTANTS, Assumptions

from src.objects.aircraft_parameters import AircraftParameters
from src.objects.lading_gear import LandingGear
from src.objects.lifting_surface_planform import LiftingSurfacePlanform
from src.objects.performance_parameters import PerformanceParameters, PerformanceAtAltitude
from src.objects.propulsion_parameters import PropulsionParameters, EngineParameters

import src.Drag.LandingGear as dlg
from src.Drag.Bay import Bay
from src.Drag.Fuselage import Fuselage
from src.Drag.Planform import Planform

def initial_state_interior():
    pe = PossibleEngines()
    MTOM = 50.
    epsilon = 1e-3
    return DesignOptionState(
        DesignOptionStateIterable(
            aircraft_parameters=AircraftParameters(
                total_mass=MTOM,
                horizontal_stabilizer_distance_from_wing=1.5,
                vertical_stabilizer_distance_from_wing=1.5,
                canard_distance_in_front_of_wing=0.,
                #NOTE required TWR to exactly match the TWR of the TJ40_G1 engine pair, with some tolerance (epsilon) to ensure float comparison
                thrust_weight_ratio=pe.engineTJ40_G1.engine_parameters.thrust_max * pe.engineTJ40_G1.n_engines / MTOM / CONSTANTS.G0 - epsilon
            ),
            lifting_surfaces=[
                LiftingSurfacePlanform(
                    aspect_ratio=20.,
                    span=4., # [m]
                    sweep_quarter_deg=25., # [m]
                    taper=.3,
                    tip_twist_rad=np.deg2rad(2.),
                ),
                LiftingSurfacePlanform(
                    aspect_ratio=3.,
                    span=.5, # [m]
                    sweep_quarter_deg=25., # [m]
                    taper=.3,
                    tip_twist_rad=np.deg2rad(2.),
                ),
                LiftingSurfacePlanform(
                    aspect_ratio=3.,
                    span=.6, # [m]
                    sweep_quarter_deg=15., # [m]
                    taper=.7,
                    tip_twist_rad=np.deg2rad(2.),
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
def initial_state():
    return initial_state_interior()

@pytest.fixture
def extendable_landing_gear_state():
    init_state = initial_state_interior()
    init_state.fixed.choices.landing_gear_sideways_extendable = True
    return init_state

@pytest.fixture
def cd0_step():
    return CD0Step()


class TestCD0Step:
    def test_bays(self, initial_state:DesignOptionState, extendable_landing_gear_state:DesignOptionState, cd0_step:CD0Step):
        bays_bay_lg = cd0_step.build_bay_components(initial_state)
        assert len(bays_bay_lg)==4
        retracting_landing_gear_height = initial_state.fixed.assumptions.main_gear_diameter_wheel / 2 + initial_state.iterable.landing_gear.length_z

        assert np.isclose(bays_bay_lg[0].length_to_diameter, initial_state.iterable.propulsion_parameters.engine_parameters.length / initial_state.iterable.propulsion_parameters.engine_parameters.diameter)
        assert np.isclose(bays_bay_lg[-1].length_to_diameter, initial_state.fixed.assumptions.lg_bay_length_safety_factor*retracting_landing_gear_height / initial_state.fixed.assumptions.lg_bay_wheel_diameter_ratio/initial_state.fixed.assumptions.main_gear_diameter_wheel)
        
        bays_no_lg = cd0_step.build_bay_components(extendable_landing_gear_state)
        assert len(bays_no_lg)==2
        assert np.isclose(bays_no_lg[0].length_to_diameter, initial_state.iterable.propulsion_parameters.engine_parameters.length / initial_state.iterable.propulsion_parameters.engine_parameters.diameter)

    def test_landing_gear(self, initial_state:DesignOptionState, extendable_landing_gear_state:DesignOptionState, cd0_step:CD0Step):
        lgs_straight_retract = cd0_step.build_landing_gear_components(initial_state)
        assert len(lgs_straight_retract)==3

        lstrut = initial_state.iterable.landing_gear.length_z - initial_state.fixed.assumptions.diameter_fuselage / 2
        lstrut = 

        drag_area_main = 0.05328 * np.exp(5.615*surface_frontal_main/surface_reference_main) * surface_reference_main


