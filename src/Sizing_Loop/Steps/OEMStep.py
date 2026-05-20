import aerosandbox as asb
import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import os
import sys

current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.append(project_root)

from src.Sizing_Loop.DesignOptionStep import DesignOptionStep
from src.Sizing_Loop.DesignOptionState import DesignOptionState
from src.Sizing_Loop.DesignOptionStateIterable import DesignOptionStateIterable
from src.MatchingDiagram.MatchingDiagramJet import MatchingDiagramJet
from src.global_parameters import CONSTANTS

class OEMStep(DesignOptionStep):
    def update(self, state:DesignOptionState) -> DesignOptionStateIterable:
        return super().update(state)