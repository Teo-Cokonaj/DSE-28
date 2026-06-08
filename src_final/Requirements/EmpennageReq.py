import sys
import os
import numpy as np
import aerosandbox as asb

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src_final.Requirements.Requirement import Requirement
from Aircraft.Aircraft import Aircraft

class EmpennageReq(Requirement):
    def __init__(self, area_ratio_maximum:float=.4):
        self.area_ratio_maximum = area_ratio_maximum

    def assess(self, aircraft:Aircraft) -> bool:
        return aircraft.planforms[1].wing_area / aircraft.planforms[0].wing_area < self.area_ratio_maximum