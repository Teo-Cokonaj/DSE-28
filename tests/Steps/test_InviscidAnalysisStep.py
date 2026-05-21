import aerosandbox as asb
import aerosandbox.numpy as np
from copy import deepcopy
import os
import sys
import pytest

current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.append(project_root)

from src.Sizing_Loop.Steps.InviscidAnalysisStep import InviscidAnalysisStep
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


class TestInviscidAnalysisStep():
    def test_InviscidAnalysisStep(self, initial_state:DesignOptionState):
        resolution = 100
        secondary_resolution = 20

        #reference
        chord = initial_state.iterable.lifting_surfaces[0].c_root
        halfspan = initial_state.iterable.lifting_surfaces[0].span / 2
        plane = asb.Airplane("single_wing", [0, 0, 0], [
                asb.Wing("the_wing", [asb.WingXSec([0, y, 0], chord, 0., SymmetricAirfoil()) for y in np.linspace(0., halfspan, resolution)], symmetric=True),
                asb.Wing("the_wing", [asb.WingXSec([0, y, 0], chord, 0., SymmetricAirfoil()) for y in np.linspace(0., halfspan, secondary_resolution)], symmetric=True).translate([10., 0., 1.]),
            ])
        #plane.draw()

        def linear_spacing(start,end,number_of_stations):
                return np.linspace(0,1,number_of_stations)

        llt_single_wing_result = LiftingLineInviscid(
            plane,
            asb.OperatingPoint(velocity=initial_state.fixed.assumptions.airspeed_approach, alpha=5.),
            spanwise_spacing_function=linear_spacing,
        ).run()
        
        invisid_ratio_reference = llt_single_wing_result["CL"]**2 / llt_single_wing_result["CD"]

        #computed
        params = InviscidAnalysisStep(wing_resolution=resolution, other_resolution=secondary_resolution).update(initial_state).performance_parameters

        assert np.isclose(params.climb_OEI_parameters.inviscid_ratio, invisid_ratio_reference, rtol=1e-1), f"{params.climb_OEI_parameters.inviscid_ratio} vs ref {invisid_ratio_reference}"
        assert np.isclose(params.takeoff_parameters.inviscid_ratio, invisid_ratio_reference, rtol=1e-1), f"{params.takeoff_parameters.inviscid_ratio} vs ref {invisid_ratio_reference}"
        assert np.isclose(params.go_around_parameters.inviscid_ratio, invisid_ratio_reference, rtol=1e-1), f"{params.go_around_parameters.inviscid_ratio} vs ref {invisid_ratio_reference}"
        assert np.isclose(params.cruise_parameters.inviscid_ratio, invisid_ratio_reference, rtol=1e-1), f"{params.cruise_parameters.inviscid_ratio} vs ref {invisid_ratio_reference}"
        assert np.isclose(params.mach_max_parameters.inviscid_ratio, invisid_ratio_reference, rtol=1e-1), f"{params.mach_max_parameters.inviscid_ratio} vs ref {invisid_ratio_reference}"