import sys
import os
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src_final.Requirements.Requirement import Requirement
from Aircraft.Aircraft import Aircraft


class MDReq(Requirement):
    def assess(self, aicraft:Aircraft) -> bool:
        pass #TODO: Connect matching diagram, check if your wing loading and thrust are sufficient
        
