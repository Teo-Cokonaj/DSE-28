import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Aircraft.Planform import Planform
from Aircraft.Fixed import Fixed

class EmpenageFinder:
    def find_empenage(planform:Planform, fixed:Fixed, stable:bool) -> Planform:
        raise NotImplementedError
        # TODO: create child classes to this class finding a tail or a canard given the planform and the fixed geometry from CAD
        # Add necessary values such as CL_H, A_H to assumptions, feel free to reuse the statistical values from the midterm, 
        # the empenage is really secondary.
