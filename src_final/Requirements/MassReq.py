import sys
import os
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src_final.Requirements.Requirement import Requirement
from Aircraft.Aircraft import Aircraft


class MassReq(Requirement):
    def assess(self, aicraft:Aircraft) -> bool:
        pass #TODO: check that the total mass of the aircraft (wing empenage fixed) is below the MTOM requirement

        
        
