import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Planform import Planform

class Replaceable:
    def __init__(self,
                 main_wing_planform: Planform,
                 horizontal_tail_planform: Planform,
                 canard_planform: Planform,
                 ):
        self.one=1