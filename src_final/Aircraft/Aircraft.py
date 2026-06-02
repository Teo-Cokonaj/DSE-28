import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Planform import Planform
from Fuselage import Fuselage
from Replaceable import Replaceable

class Aircraft:
    def __init__(self,
                 fuselage: Fuselage,
                 replaceable: Replaceable
                 ):
        self.one=1