import aerosandbox as asb
import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import os
import sys

current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.append(project_root)

from src.Sizing_Loop.DesignOptionStep import DesignOptionStep
from src.Sizing_Loop.DesignOptionState import DesignOptionState
from src.Sizing_Loop.DesignOptionStateIterable import DesignOptionStateIterable
from src.MatchingDiagram.MatchingDiagramJet import MatchingDiagramJet
from src.global_parameters import CONSTANTS

class MatchingDiagramStep(DesignOptionStep):
    def __init__(self, resolution:int=100, plot:bool=False, location_legend:str="upper left"):
        self.resolution = resolution
        self.plot = plot
        self.location_legend = location_legend

    def update(self, state:DesignOptionState) -> DesignOptionStateIterable:
        diagram = MatchingDiagramJet(state.iterable.propulsion_parameters.n_engines, resolution=self.resolution)

        CL_max = state.CL_max()

        diagram.add_landing_field_length("Landing Length", state.fixed.assumptions.airfield_length, CL_max)
        diagram.create_wing_loading_axis()

        diagram.add_cruise_speed(
            constraint_label = "Mach max", 
            mach = CONSTANTS.MACH_MAX, 
            CD0 = state.iterable.performance_parameters.mach_max_parameters.CD0,
            inviscid_ratio = state.iterable.performance_parameters.mach_max_parameters.inviscid_ratio,
            atmosphere = asb.Atmosphere(CONSTANTS.ALTITUDE_MACH_MAX),
            beta = (1 - state.iterable.aircraft_parameters.fuel_mass_fraction / 2) #NOTE: we must be able to perform mach max half-fuelled
        )
        diagram.add_cruise_speed(
            constraint_label = "Cruise speed",
            mach = CONSTANTS.MACH_CRUISE,
            CD0 = state.iterable.performance_parameters.cruise_parameters.CD0,
            inviscid_ratio = state.iterable.performance_parameters.cruise_parameters.inviscid_ratio,
            atmosphere = asb.Atmosphere(state.fixed.assumptions.ALTITUDE_CRUISE)
        )

        diagram.add_climb_gradient(
            constraint_label = "Climb gradient AEO",
            tan_gradient = CONSTANTS.CLIMB_GRADIENT_AEO,
            CD0 = state.iterable.performance_parameters.takeoff_parameters.CD0,
            inviscid_ratio = state.iterable.performance_parameters.takeoff_parameters.inviscid_ratio,
            all_engines_operative = True,
            atmosphere = asb.Atmosphere(0.)
        )
        diagram.add_climb_gradient(
            constraint_label = "Climb gradient OEI",
            tan_gradient = CONSTANTS.CLIMB_GRADIENT_OEI,
            CD0 = state.iterable.performance_parameters.climb_OEI_parameters.CD0,
            inviscid_ratio = state.iterable.performance_parameters.climb_OEI_parameters.inviscid_ratio,
            all_engines_operative = False,
            atmosphere = asb.Atmosphere(CONSTANTS.ALTITUDE_OEI_CLIMB)
        )
        #NOTE: there is also a 3% climb gradient on balked landing in the landing configuration, but since our Toff and landing configs are same (no HLDs), we skip that one

        diagram.add_takeoff_field_length(
            constraint_label = "Takeoff length", 
            field_length = state.fixed.assumptions.airfield_length,
            inviscid_ratio = state.iterable.performance_parameters.takeoff_parameters.inviscid_ratio,
            CL_takeoff = CL_max
        )

        wing_loading, thrust_weight = diagram.select_design_point(lambda wing_loading, thrust_weight: thrust_weight)

        MatchingDiagramStep._update_wing_areas(state, wing_loading)
        state.iterable.aircraft_parameters.thrust_weight_ratio = thrust_weight

        if self.plot:
            diagram.plot(wing_loading, thrust_weight, self.location_legend)
            plt.show()

        return state.iterable


    @staticmethod
    def _update_wing_areas(state:DesignOptionState, wing_loading:float):
        new_surface = state.iterable.aircraft_parameters.total_mass * CONSTANTS.G0 / wing_loading
        surface_ratio = new_surface / state.iterable.lifting_surfaces[0].wing_area

        for lifting_surface in state.iterable.lifting_surfaces:
            lifting_surface.wing_area *= surface_ratio