import sys
import os
import typing as ty
import numpy.typing as nt
import aerosandbox.numpy as np
import copy

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Sizing_Loop.DesignOptionState import DesignOptionState
from src.Sizing_Loop.DesignOptionStep import DesignOptionStep
from src.Sizing_Loop.DesignOption import DesignOption
from src.Sizing_Loop.DesignOptionChoices import DesignOptionChoices
from src.Sizing_Loop.DesignOptionStateFixed import DesignOptionStateFixed
from src.Sizing_Loop.DesignOptionStateIterable import DesignOptionStateIterable

from src.Sizing_Loop.Steps.MatchingDiagramStep import MatchingDiagramStep
from src.Sizing_Loop.Steps.CD0Step import CD0Step
from src.Sizing_Loop.Steps.WeightEstimationStep import WeightEstimationStep
from src.Sizing_Loop.Steps.InviscidAnalysisStep import InviscidAnalysisStep
from src.Sizing_Loop.Steps.tail_sizing_step import TailSizingStep
from src.Sizing_Loop.Steps.EngineSelectionStep import EngineSelectionStep
from src.Sizing_Loop.Steps.LandingGearStep import LandingGearStep

from src.global_parameters import Assumptions
import src.ac_stats as stat

from src.objects.aircraft_parameters import AircraftParameters
from src.objects.lading_gear import LandingGear
from src.objects.lifting_surface_planform import LiftingSurfacePlanform
from src.objects.performance_parameters import PerformanceParameters, PerformanceAtAltitude
from src.objects.possible_engines import PossibleEngines

class SizingForTradeoff():
    def __init__(self):
        self.configurations = [

            DesignOptionChoices(
                name="HUG-CFG-301",
                canard_capability=True, 
                landing_gear_sideways_extendable=True,
                wing_interference_factor=1.2,
                main_wing_x_movable=True
            ),

            DesignOptionChoices(
                name="HUG-CFG-302",
                canard_capability=False,
                landing_gear_sideways_extendable=False,
                wing_interference_factor=1.0,
                main_wing_x_movable=False
            ),

            DesignOptionChoices(
                name="HUG-CFG-303",
                canard_capability=True,
                landing_gear_sideways_extendable=True,
                wing_interference_factor=1.0,
                main_wing_x_movable=False
            ),

            DesignOptionChoices(
                name="HUG-CFG-304",
                canard_capability=True,
                landing_gear_sideways_extendable=False,
                wing_interference_factor=1.0,
                main_wing_x_movable=True
            ),

            DesignOptionChoices(
                name="HUG-CFG-305",
                canard_capability=True,
                landing_gear_sideways_extendable=True,
                wing_interference_factor=1.0,
                main_wing_x_movable=True
            )
        ]

        self.assumptions = Assumptions()

        self.initial_condition = DesignOptionStateIterable(
            aircraft_parameters=AircraftParameters(
                total_mass=50.,
                horizontal_stabilizer_distance_from_wing=1.5,
                vertical_stabilizer_distance_from_wing=1.5,
                canard_distance_in_front_of_wing=0.,
                empty_mass_fraction=870 / 1008
            ),
            lifting_surfaces=[
                LiftingSurfacePlanform(
                    aspect_ratio=stat.AR_HUGO,
                    span=stat.b_HUGO, # [m]
                    sweep_quarter_deg=stat.Lambda_qc_HUGO, # [m]
                    taper=stat.lambda_HUGO,
                    tip_twist_rad=stat.tip_twist_HUGO,
                ),
                LiftingSurfacePlanform(
                    aspect_ratio=stat.HT_AR_HUGO,
                    span=stat.HT_span_HUGO, # [m]
                    sweep_quarter_deg=stat.HT_sweep_quarter_deg_HUGO, # [m]
                    taper=stat.HT_taper_HUGO,
                    tip_twist_rad=0.,
                ),
                LiftingSurfacePlanform(
                    aspect_ratio=stat.VT_AR_HUGO,
                    span=stat.b_HUGO, # [m]
                    sweep_quarter_deg=stat.VT_sweep_quarter_deg_HUGO, # [m]
                    taper=stat.VT_taper_HUGO,
                    tip_twist_rad=0.,
                )
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

        self.steps:list[DesignOptionStep] = list()

    
    def accumulate_steps(self, debug:bool=False, plot:bool=False, resolution_matching_diagram:int=100, legend_location_matching_diagram:str="upper left", inviscid_analysis_sample_aoa_deg:float=5., wing_resolution:int=100, secondary_planforms_resolution:int=5):
        self.steps = [
            TailSizingStep(debug, wing_resolution, secondary_planforms_resolution),
            InviscidAnalysisStep(plot, debug, inviscid_analysis_sample_aoa_deg, wing_resolution, secondary_planforms_resolution),
            WeightEstimationStep(debug),
            MatchingDiagramStep(resolution_matching_diagram, plot, legend_location_matching_diagram),
            EngineSelectionStep(debug),
            LandingGearStep(debug),
            CD0Step()
        ]

    
    def size_options_for_tradeoff(self, n_iteration_steps:int, convergence_criterion:ty.Callable[[DesignOptionState], nt.NDArray[np.float64]]) -> list[tuple[DesignOption, list[nt.NDArray[np.float64]]]]:
        sizing_results:list[tuple[DesignOption, list[nt.NDArray[np.float64]]]] = list()

        for configuration in self.configurations:
            design_option = DesignOption(
                DesignOptionState(
                    iterable=copy.deepcopy(self.initial_condition), 
                    _fixed=DesignOptionStateFixed(
                        assumptions=self.assumptions,
                        choices=configuration
                    )
                ),
                self.steps
            )

            convergence_history = design_option.iterate_for_n_steps(n_iteration_steps, convergence_criterion)
            sizing_results.append((design_option, convergence_history))

        return sizing_results
    

    def sweep_wrt_parameter(self, parameter_setter:ty.Callable[[Assumptions, object], Assumptions], parameter_range:list, 
        n_iteration_steps:int, convergence_criterion:ty.Callable[[DesignOptionState], nt.NDArray[np.float64]]) -> list[list[nt.NDArray[np.float64]]]:
        sweep_results:list[list[nt.NDArray[np.float64]]] = list()

        for parameter_value in parameter_range:
            assumptions_modified = parameter_setter(copy.deepcopy(self.assumptions), parameter_value)
            sizing_result_for_param:list[nt.NDArray[np.float64]] = list()

            for configuration in self.configurations:
                design_option = DesignOption(
                    DesignOptionState(
                        iterable=copy.deepcopy(self.initial_condition), 
                        _fixed=DesignOptionStateFixed(
                            assumptions=assumptions_modified,
                            choices=configuration
                        )
                    ),
                    self.steps
                )

                convergence_history = design_option.iterate_for_n_steps(n_iteration_steps, convergence_criterion)
                sizing_result_for_param.append(convergence_history[:, -1])
        
            sweep_results.append(sizing_result_for_param)

        return sweep_results
            