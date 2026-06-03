import sys
import os
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src_final.Requirements.Requirement import Requirement
from Aircraft.Aircraft import Aircraft


class FuelReq(Requirement):
    def assess(self, aicraft:Aircraft) -> bool:
        pass #TODO: connect the fuel estimation. Check if the fuselage fuel tanks have enough fuel
        
