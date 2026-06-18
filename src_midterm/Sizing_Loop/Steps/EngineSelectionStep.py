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
from src.objects.possible_engines import PossibleEngines
from src.objects.propulsion_parameters import PropulsionParameters, EngineParameters
from src.global_parameters import CONSTANTS

class EngineSelectionStep(DesignOptionStep):
    def __init__(self, print_:bool=False):
        self.print_ = print_


    def update(self, state:DesignOptionState) -> DesignOptionStateIterable:
        thrust_weight = state.iterable.aircraft_parameters.thrust_weight_ratio
        weight = state.iterable.aircraft_parameters.total_mass * CONSTANTS.G0
        thrust_minimum = thrust_weight * weight

        if self.print_:
            print(f"Thrust minimum: {thrust_minimum}")

        feasible_engines:list[PropulsionParameters] = list()
        feasible_engine_names = list()
        for engine_name,  possible_engine in PossibleEngines().__dict__.items():
            if possible_engine.engine_parameters.thrust_max * possible_engine.n_engines > thrust_minimum:
                feasible_engines.append(possible_engine)
                feasible_engine_names.append(engine_name)
        
        feasible_engine_masses = [engine.engine_parameters.mass for engine in feasible_engines]
        selected_engine_index = np.argmin(feasible_engine_masses)
        
        if self.print_:
            print(f"Selected engine: {feasible_engine_names[selected_engine_index]}")
        
        state.iterable.propulsion_parameters = feasible_engines[selected_engine_index]
        return state.iterable