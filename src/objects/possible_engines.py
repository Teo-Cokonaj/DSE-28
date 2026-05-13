import os
import sys

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.objects.propulsion_parameters import EngineParameters, PropulsionParameters

class PossibleEngines:
    def __init__(self):
        self.jetcatExample = PropulsionParameters(EngineParameters(
            thrust_max=250, # [N]
            diameter=.2, # [m]
            length=.5, # [m]
            efficiency_total=.6 # [-] NOTE: thrmal_efficiency*propulsive_efficiency
        ), 2)