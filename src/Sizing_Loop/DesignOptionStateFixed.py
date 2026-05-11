from dataclasses import dataclass

import sys
import os

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.global_parameters import Assumptions
from src.Sizing_Loop.DesignOptionChoices import DesignOptionChoices

@dataclass
class DesignOptionStateFixed:
    assumptions:Assumptions = Assumptions()
    choices:DesignOptionChoices = DesignOptionChoices()
