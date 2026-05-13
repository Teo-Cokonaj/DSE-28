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
from src.Sizing_Loop.Steps.WeightEstimationStep import WeightEstimationStep
from src.Sizing_Loop.Steps.InviscidAnalysisStep import InviscidAnalysisStep
from src.Sizing_Loop.Steps.tail_sizing_step import TailSizingStep

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
            propulsion_parameters=PropulsionParameters(EngineParameters(250., .1, .5), 2),
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

class TestDesignOption:
    def test_twoIterations(self, initial_state, print_:bool=False, plot:bool=False):
        matching_diagram_step = MatchingDiagramStep(plot=plot)
        CD0_step = CD0Step()
        class_I_step = WeightEstimationStep(print_)
        inviscid_step = InviscidAnalysisStep()
        tail_sizing_step = TailSizingStep()

        design_option = DesignOption(initial_state, [inviscid_step, class_I_step, matching_diagram_step, CD0_step, tail_sizing_step])
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
            print("\nclimb at OEI performance")
            print(design_option.state.iterable.performance_parameters.climb_OEI_parameters.glide_ratio_max())
            print(design_option.state.iterable.performance_parameters.climb_OEI_parameters.CL_glide_ratio_max())
            print(design_option.state.iterable.performance_parameters.climb_OEI_parameters.CD0)
            print(design_option.state.iterable.performance_parameters.climb_OEI_parameters.inviscid_ratio)
            print("\ntakeoff performance")
            print(design_option.state.iterable.performance_parameters.takeoff_parameters.glide_ratio_max())
            print(design_option.state.iterable.performance_parameters.takeoff_parameters.CL_glide_ratio_max())
            print(design_option.state.iterable.performance_parameters.takeoff_parameters.CD0)
            print(design_option.state.iterable.performance_parameters.takeoff_parameters.inviscid_ratio)
            print("\nmach max")
            print(design_option.state.iterable.performance_parameters.mach_max_parameters.glide_ratio_max())
            print(design_option.state.iterable.performance_parameters.mach_max_parameters.CL_glide_ratio_max())
            print(design_option.state.iterable.performance_parameters.mach_max_parameters.CD0)
            print(design_option.state.iterable.performance_parameters.mach_max_parameters.inviscid_ratio)
            

    
if __name__ == "__main__":
    test_design_option = TestDesignOption()
    test_design_option.test_twoIterations(initial_state_interior(), True, True)