import aerosandbox as asb
import aerosandbox.numpy as np
from copy import deepcopy
import os
import sys
import pytest

current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.append(project_root)

from src.Sizing_Loop.Steps.MatchingDiagramStep import MatchingDiagramStep
from src.Sizing_Loop.DesignOptionState import DesignOptionState
from src.Sizing_Loop.DesignOptionStateIterable import DesignOptionStateIterable
from src.MatchingDiagram.ThrustLapse import ThrustLapse
from src.global_parameters import CONSTANTS

from src.objects.aircraft_parameters import AircraftParameters
from src.objects.lifting_surface_planform import LiftingSurfacePlanform
from src.objects.performance_parameters import PerformanceParameters, PerformanceAtAltitude
from src.objects.propulsion_parameters import PropulsionParameters, EngineParameters

def initial_state_interior():
    return DesignOptionState(
        DesignOptionStateIterable(
            aircraft_parameters=AircraftParameters(
                total_mass=50.,
                horizontal_stabilizer_distance_from_wing=1.5,
                vertical_stabilizer_distance_from_wing=1.5,
                canard_distance_in_front_of_wing=0.,
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
            propulsion_parameters=PropulsionParameters(EngineParameters(250., .1, .5, .12), 2),
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


class TestMatchingDiagramStep():
    def test_with_analytical_TW(self, initial_state:DesignOptionState):
        #reference
        wing_loading_constraint = initial_state.fixed.assumptions.airspeed_stall**2 * CONSTANTS.AIR_DENSITY_SEA_LEVEL / 2 * initial_state.CL_max()

        atmosphere_mach_max = asb.Atmosphere(CONSTANTS.ALTITUDE_MACH_MAX)
        thrust_lapse = ThrustLapse(atmosphere_mach_max).thrust_lapse(CONSTANTS.MACH_MAX)
        CL_mach_max = wing_loading_constraint * 2 / atmosphere_mach_max.density() / (atmosphere_mach_max.speed_of_sound() * CONSTANTS.MACH_MAX)**2
        CD0_mach_max = initial_state.iterable.performance_parameters.mach_max_parameters.CD0
        inviscid_ratio_mach_max = initial_state.iterable.performance_parameters.mach_max_parameters.inviscid_ratio
        CD_CL_mach_max = CD0_mach_max / CL_mach_max + CL_mach_max / inviscid_ratio_mach_max
        thrust_weight_mach_max = CD_CL_mach_max / thrust_lapse

        old_tail_area_ratios = [planform.wing_area / initial_state.iterable.lifting_surfaces[0].wing_area 
                                for planform in initial_state.iterable.lifting_surfaces]

        #computed
        matching_diagram_step = MatchingDiagramStep()
        new_state = deepcopy(initial_state)
        new_state.iterable = matching_diagram_step.update(initial_state)

        assert np.isclose(new_state.wing_loading(), wing_loading_constraint, atol=matching_diagram_step.resolution), f"{new_state.wing_loading()} vs ref {wing_loading_constraint}"

        new_thrust_weight = new_state.iterable.aircraft_parameters.thrust_weight_ratio
        assert np.isclose(new_thrust_weight, thrust_weight_mach_max, rtol=1/matching_diagram_step.resolution), f"{new_thrust_weight} vs ref {thrust_weight_mach_max}"

        new_tail_area_ratios = [planform.wing_area / new_state.iterable.lifting_surfaces[0].wing_area 
                                for planform in new_state.iterable.lifting_surfaces]
        assert np.allclose(new_tail_area_ratios, old_tail_area_ratios), f"""{new_tail_area_ratios} vs {old_tail_area_ratios};\n
        ratios between lifting surface areas shouldn't change in this step!!!"""
