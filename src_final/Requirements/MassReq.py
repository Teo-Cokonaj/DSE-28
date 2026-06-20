import sys
import os
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src_final.Requirements.Requirement import Requirement
from Aircraft.Aircraft import Aircraft


class MassReq(Requirement):

    def __init__(self, mtow_max):
        self.mtow_max = mtow_max

    def assess(self, aircraft:Aircraft) -> bool:
        self.aircraft_mass = aircraft.total_mass()

        return self.aircraft_mass <= self.mtow_max
        
       