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
            sfc=0.153/3600, # [-] NOTE: thrmal_efficiency*propulsive_efficiency
            mass = 3.4 # [kg]
        ), 2)
        self.engineTJ40_G2 = PropulsionParameters(EngineParameters(
            thrust_max=425, # [N]
            diameter=.147, # [m]
            length=.373, # [m]
            sfc=0.153/3600, # [-] NOTE: thrmal_efficiency*propulsive_efficiency
            mass = 3.8 # [kg]
        ), 2)
        self.engineTJ80_90 = PropulsionParameters(EngineParameters(
            thrust_max=900, # [N]
            diameter=.235, # [m]
            length=.511, # [m]
            sfc=0.151/3600, # [-] NOTE: thrmal_efficiency*propulsive_efficiency
            mass = 12.5 # [kg]
        ), 2)
        self.engineTJ80_120 = PropulsionParameters(EngineParameters(
            thrust_max=1200, # [N]
            diameter=.235, # [m]
            length=.512, # [m]
            sfc=0.13/3600, # [-] NOTE: thrmal_efficiency*propulsive_efficiency
            mass = 13.0 # [kg]
        ), 2)
        self.engineP1000_PRO_S_GH = PropulsionParameters(EngineParameters(
            thrust_max=1100, # [N]
            diameter=.234, # [m]
            length=.505, # [m]
            sfc=2.900/3600, # [-] NOTE: thrmal_efficiency*propulsive_efficiency
            mass = 11.57 # [kg]
        ), 2)
        self.engineP190_PRO_S = PropulsionParameters(EngineParameters(
            thrust_max=190, # [N] 
            diameter=.108, # [m]
            length=.301, # [m]
            sfc=0.158/3600, # [-] NOTE: thermal_efficiency*propulsive_efficiency
            mass=1.90 # [kg]
        ), 2)
        self.engineP220_PRO = PropulsionParameters(EngineParameters(
            thrust_max=220, # [N] 
            diameter=.117, # [m]
            length=.474, # [m] (Note: Length ranges from 0.215m to 0.474m depending on standard vs extended nozzle)
            sfc=0.158/3600, # [-] NOTE: thermal_efficiency*propulsive_efficiency
            mass=2.16 # [kg] (Note: Mass ranges from 1.85kg to 2.16kg depending on nozzle configuration)
        ), 2)
        self.engineP250_PRO_S = PropulsionParameters(EngineParameters(
            thrust_max=250, # [N]
            diameter=.121, # [m]
            length=.323, # [m]
            sfc=0.158/3600, # [-] NOTE: thermal_efficiency*propulsive_efficiency
            mass=2.155 # [kg]
        ), 2)

        self.engineP300_PRO_S = PropulsionParameters(EngineParameters(
            thrust_max=300, # [N]
            diameter=.132, # [m]
            length=.381, # [m]
            sfc=0.157/3600, # [-] NOTE: thermal_efficiency*propulsive_efficiency
            mass=2.73 # [kg]
        ), 2)

        self.engineP350_PRO_S = PropulsionParameters(EngineParameters(
            thrust_max=360, # [N]
            diameter=.136, # [m]
            length=.350, # [m]
            sfc=0.158/3600, # [-] NOTE: thermal_efficiency*propulsive_efficiency
            mass=2.89 # [kg]
        ), 2)

        self.engineP400_PRO_S = PropulsionParameters(EngineParameters(
            thrust_max=425, # [N] (Latest standard PRO outputs up to 425N; older units are 397N)
            diameter=.148, # [m]
            length=.390, # [m]
            sfc=0.158/3600, # [-] NOTE: thermal_efficiency*propulsive_efficiency
            mass=4.14 # [kg]
        ), 2)

        self.engineP500_PRO_S = PropulsionParameters(EngineParameters(
            thrust_max=492, # [N] 
            diameter=.175, # [m]
            length=.419, # [m]
            sfc=0.151/3600, # [-] NOTE: thermal_efficiency*propulsive_efficiency
            mass=5.4 # [kg]
        ), 2)

        self.engineP550_PRO_S = PropulsionParameters(EngineParameters(
            thrust_max=550, # [N]
            diameter=.175, # [m]
            length=.416, # [m]
            sfc=0.141/3600, # [-] NOTE: thermal_efficiency*propulsive_efficiency
            mass=5.4 # [kg]
        ), 2)

        self.engine_for_overflows = PropulsionParameters(EngineParameters(
            thrust_max=25000, # [N]
            diameter=.175, # [m]
            length=.416, # [m]
            sfc=0.151/3600, # [-] NOTE: thermal_efficiency*propulsive_efficiency
            mass=10. # [kg]
        ), 2)

        self.engineP100_RX = PropulsionParameters(EngineParameters(
            thrust_max=100, # [N]
            diameter=.097, # [m]
            length=.241, # [m]
            sfc=0.187/3600, # [-] NOTE: thermal_efficiency*propulsive_efficiency
            mass=1.08 # [kg]
        ), 2)

        self.engineP130_RX = PropulsionParameters(EngineParameters(
            thrust_max=130, # [N] 
            diameter=.099, # [m]
            length=.284, # [m]
            sfc=0.185/3600, # [-] NOTE: thermal_efficiency*propulsive_efficiency
            mass=1.326 # [kg]
        ), 2)

        self.engineP150_RX = PropulsionParameters(EngineParameters(
            thrust_max=150, # [N] 
            diameter=.099, # [m]
            length=.284, # [m]
            sfc=0.185/3600, # [-] NOTE: thermal_efficiency*propulsive_efficiency
            mass=1.326 # [kg]
        ), 2)
