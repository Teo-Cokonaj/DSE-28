import aerosandbox as asb
import aerosandbox.numpy as np
from copy import deepcopy
import os
import sys
import pytest

current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.append(project_root)

from src.Sizing_Loop.Steps.EngineSelectionStep import EngineSelectionStep
from src.objects.possible_engines import PossibleEngines
from src.Sizing_Loop.DesignOptionState import DesignOptionState
from src.Sizing_Loop.DesignOptionStateIterable import DesignOptionStateIterable
from src.global_parameters import CONSTANTS, Assumptions

from src.objects.aircraft_parameters import AircraftParameters
from src.objects.lading_gear import LandingGear
from src.objects.lifting_surface_planform import LiftingSurfacePlanform
from src.objects.performance_parameters import PerformanceParameters, PerformanceAtAltitude
from src.objects.propulsion_parameters import PropulsionParameters, EngineParameters

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


class TestEngineSelectionStep:
    def test_engine_selection(self, initial_state:DesignOptionState):
        propulsion_reference = PossibleEngines().engineTJ40_G1

        engine_selection_step = EngineSelectionStep()
        initial_state.iterable = engine_selection_step.update(initial_state)
        propulsion_result = initial_state.iterable.propulsion_parameters

        assert propulsion_result.n_engines == propulsion_reference.n_engines
        assert np.isclose(propulsion_result.engine_parameters.efficiency_total, propulsion_reference.engine_parameters.efficiency_total)
        assert np.isclose(propulsion_result.engine_parameters.thrust_max, propulsion_reference.engine_parameters.thrust_max)
        assert np.isclose(propulsion_result.engine_parameters.mass, propulsion_reference.engine_parameters.mass)
        assert np.isclose(propulsion_result.engine_parameters.length, propulsion_reference.engine_parameters.length)
        assert np.isclose(propulsion_result.engine_parameters.diameter, propulsion_reference.engine_parameters.diameter)
        