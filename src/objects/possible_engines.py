import os
import sys

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.objects.propulsion_parameters import EngineParameters, PropulsionParameters
# THE ENGINE EFFICIENCIES ARE NOT VERIFIED, I NEED TO FIND A WAY TO CALCULATE OR ESTIMATE THEM
class PossibleEngines:
    def __init__(self):
        self.engineTJ40_G1 = PropulsionParameters(EngineParameters(
            thrust_max=425, # [N]
            diameter=.147, # [m]
            length=.304, # [m]
            efficiency_total=.1, # [-] NOTE: thrmal_efficiency*propulsive_efficiency
            mass = 3.4 # [kg]
        ), 2)
        self.engineTJ40_G2 = PropulsionParameters(EngineParameters(
            thrust_max=425, # [N]
            diameter=.147, # [m]
            length=.373, # [m]
            efficiency_total=.1, # [-] NOTE: thrmal_efficiency*propulsive_efficiency
            mass = 3.8 # [kg]
        ), 2)
        # self.engineTJ80_90 = PropulsionParameters(EngineParameters(
        #     thrust_max=900, # [N]
        #     diameter=.235, # [m]
        #     length=.511, # [m]
        #     efficiency_total=.15, # [-] NOTE: thrmal_efficiency*propulsive_efficiency
        #     mass = 12.5 # [kg]
        # ), 1)
        # self.engineTJ80_120 = PropulsionParameters(EngineParameters(
        #     thrust_max=1200, # [N]
        #     diameter=.235, # [m]
        #     length=.512, # [m]
        #     efficiency_total=.15, # [-] NOTE: thrmal_efficiency*propulsive_efficiency
        #     mass = 13.0 # [kg]
        # ), 1)
        self.engineP500_PRO_S_GH = PropulsionParameters(EngineParameters(
            thrust_max=492, # [N]
            diameter=.175, # [m]
            length=.416, # [m]
            efficiency_total=.1, # [-] NOTE: thrmal_efficiency*propulsive_efficiency
            mass = 5.4 # [kg]
        ), 2)
        # self.engineP1000_PRO_S_GH = PropulsionParameters(EngineParameters(
        #     thrust_max=1100, # [N]
        #     diameter=.234, # [m]
        #     length=.505, # [m]
        #     efficiency_total=.15, # [-] NOTE: thrmal_efficiency*propulsive_efficiency
        #     mass = 11.57 # [kg]
        # ), 1)