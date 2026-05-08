import aerosandbox as asb
import os
import sys

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.MatchingDiagram.MatchingDiagram import MatchingDiagram
from src.global_parameters import CONSTANTS

class MatchingDiagramJet(MatchingDiagram):
    def __init__(self):
        pass