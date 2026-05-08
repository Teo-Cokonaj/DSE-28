import os
import sys
import aerosandbox.numpy as np
import typing as ty
import matplotlib.pyplot as plt
import matplotlib

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class MatchingDiagram():
    def __init__(self, constraints_thrust:dict[str, ty.Callable[[float], float]], constraints_wing_loading:dict[str, float], resolution:int=100):
        self.constraints_thrust = constraints_thrust
        self.constraints_wing_loading = constraints_wing_loading
        self.resolution = resolution

        cutoff_wing_loading = min(self.constraints_wing_loading.values())
        self.wing_loadings = np.linspace(0., cutoff_wing_loading, resolution)
        

    def plot(self, selected_wing_loading:float=None, selected_thrust_weight:float=None, location_legend:str=None) -> matplotlib.figure.Figure:
        figure = plt.figure()

        for key, value in self.constraints_thrust.items():
            plt.plot(self.wing_loadings, [value(wing_loading) for wing_loading in self.wing_loadings], label=key)

        for key, value in self.constraints_wing_loading.items():
            plt.plot([value, value], [0., 1.], label=key)

        if not (selected_wing_loading is None or selected_thrust_weight is None):
            plt.scatter([selected_wing_loading], [selected_thrust_weight], label="Selected Design Point")
        
        if location_legend is None:
            plt.legend()
        else:
            plt.legend(loc=location_legend)

        plt.xlabel(r"Wing Loading [N/m$^2$]")
        plt.ylabel("Thrust-Weight Ratio [-]")
        return figure

    
    def select_design_point(self, penalty_function:ty.Callable[[float, float], float])->tuple[float, float]:

        thrust_weight_ratios = [max(constraint(wing_loading) for constraint in self.constraints_thrust.values()) for wing_loading in self.wing_loadings]

        rank_for_design_points = [penalty_function(wing_loading, thrust_weight) 
                                  for wing_loading, thrust_weight in zip(self.wing_loadings, thrust_weight_ratios)]
        index_best_design_point = np.argmin(rank_for_design_points)

        return self.wing_loadings[index_best_design_point], thrust_weight_ratios[index_best_design_point]
        