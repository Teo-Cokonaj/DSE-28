import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Aircraft.Planform import Planform
from Aircraft.Fixed import Fixed

class Aircraft:
    def __init__(self,
                 fixed: Fixed,
                 planforms:list[Planform]
                 ):
        self.fixed = fixed
        self.planforms = planforms