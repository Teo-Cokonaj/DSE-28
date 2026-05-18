import aerosandbox as asb
import aerosandbox.numpy as np
from copy import deepcopy
import os
import sys
import pytest

current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.append(project_root)

from src.Sizing_Loop.Steps.WeightEstimationStep import WeightEstimationStep
from src.Sizing_Loop.DesignOptionState import DesignOptionState
from src.Sizing_Loop.DesignOptionStateIterable import DesignOptionStateIterable
from src.Class_I.fuel_mass_fraction import fuel_mass_fraction
from src.global_parameters import CONSTANTS, Assumptions

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
            propulsion_parameters=PropulsionParameters(EngineParameters(250., .1, .5, .15), 2),
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

class TestWeightEstimationStep():
    def test_weight_estimation_step(self, initial_state:DesignOptionState, debug:bool=False):
        #reference
        assumptions = Assumptions()
        fuel_fraction = fuel_mass_fraction(
            altitude_go_around=assumptions.ALTITUDE_GO_AROUND,
            altitude_cruise=assumptions.ALTITUDE_CRUISE,
            CL_max_glide_ratio_go_around=initial_state.iterable.performance_parameters.go_around_parameters.CL_glide_ratio_max(),
            glide_ratio_cruise=initial_state.glide_ratio_cruise(),
            glide_ratio_mach_max=initial_state.glide_ratio_mach_max(),
            glide_ratio_go_around=initial_state.iterable.performance_parameters.go_around_parameters.glide_ratio_max(),
            airspeed_approach=assumptions.airspeed_approach,
            wing_loading=initial_state.wing_loading(),
            efficiency_engine_total=initial_state.iterable.propulsion_parameters.engine_parameters.efficiency_total,
            energy_density_saf=assumptions.energy_density_saf,
            time_half_turn=assumptions.TIME_HALF_CIRCLE,
            debug=debug
        )
        oem_fraction = initial_state.iterable.aircraft_parameters.empty_mass_fraction

        mtom_reference = CONSTANTS.MASS_PAYLOAD / (1 - oem_fraction - fuel_fraction)

        #computed
        weight_estimation_step = WeightEstimationStep()
        new_state = deepcopy(initial_state)
        new_state.iterable = weight_estimation_step.update(initial_state)

        new_mtom = new_state.iterable.aircraft_parameters.total_mass
        assert np.isclose(new_mtom, mtom_reference), f"{new_mtom} vs ref {mtom_reference}"

        assert np.isclose(new_state.iterable.aircraft_parameters.empty_mass_fraction, oem_fraction), f"OEM shouldn't change !!!"
        
        new_fuel_fraction = new_state.iterable.aircraft_parameters.fuel_mass_fraction
        assert np.isclose(new_fuel_fraction, fuel_fraction), f"{new_fuel_fraction} vs ref {fuel_fraction}"

        if debug:
            print(initial_state.glide_ratio_cruise())
            print(initial_state.glide_ratio_mach_max())
            print(initial_state.CL_cruise())
            print(initial_state.CL_mach_max())
            print(new_mtom)
            print(fuel_fraction)


if __name__ == "__main__":
    TestWeightEstimationStep().test_weight_estimation_step(initial_state_interior(), True)