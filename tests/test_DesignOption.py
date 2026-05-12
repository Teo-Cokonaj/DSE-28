import pytest as pt
import aerosandbox.numpy as np
import sys
import os
import matplotlib.pyplot as plt
import pytest
import aerosandbox as asb

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Sizing_Loop.DesignOption import DesignOption
from src.Sizing_Loop.DesignOptionState import DesignOptionState
from src.Sizing_Loop.DesignOptionStateIterable import DesignOptionStateIterable
from src.Sizing_Loop.Steps.MatchingDiagramStep import MatchingDiagramStep
from src.Sizing_Loop.Steps.CD0Step import CD0Step

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
                )
            ],
            propulsion_parameters=PropulsionParameters(EngineParameters(250., .1, .5), 2),
            performance_parameters=PerformanceParameters(
                cruise_parameters=PerformanceAtAltitude(np.pi*.8*20., .01),
                mach_max_parameters=PerformanceAtAltitude(np.pi*.75*20., .02),
                go_around_parameters=PerformanceAtAltitude(np.pi*.9*20., .015),
                takeoff_parameters=PerformanceAtAltitude(np.pi*.9*20., .025)
            )
        )
    )


@pytest.fixture
def initial_state():
    return initial_state_interior()

class TestDesignOption:
    def test_twoIterations(self, initial_state, print_:bool=False, plot:bool=False):
        matching_diagram_step = MatchingDiagramStep(plot=plot)
        CD0_step = CD0Step()

        design_option = DesignOption(initial_state, [matching_diagram_step, CD0_step])
        design_option.iteration_step()

        #checking that the iteration actually happened
        assert not np.isclose(design_option.state.iterable.lifting_surfaces[0].span, 4.)
        assert not np.isclose(design_option.state.iterable.lifting_surfaces[1].span, .5)
        assert not np.isclose(design_option.state.iterable.aircraft_parameters.thrust_weight_ratio, 0.)

        if print_:
            print(design_option.state.iterable.lifting_surfaces[0].span)
            print(design_option.state.iterable.lifting_surfaces[0].wing_area)
            print(design_option.state.iterable.lifting_surfaces[1].span)
            print(design_option.state.iterable.aircraft_parameters.thrust_weight_ratio)

    
if __name__ == "__main__":
    test_design_option = TestDesignOption()
    test_design_option.test_twoIterations(initial_state_interior(), True, True)