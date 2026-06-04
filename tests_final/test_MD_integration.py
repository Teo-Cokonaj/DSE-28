import sys
import os
import numpy as np
import aerosandbox as asb
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src_final.Requirements.Requirement import Requirement
from src_final.Aircraft.Aircraft import Aircraft
from src_final.Aircraft.Planform import Planform
from src_final.Aircraft.Fixed import Fixed
from src_final.MatchingDiagram.MatchingDiagramJet import MatchingDiagramJet
from src_final.global_parameters import CONSTANTS, Assumptions

wing = Planform(
    aspect_ratio=27.0,
    span=4.0,
    sweep_quarter_deg=25.0,
    taper=0.4,
    thickness_to_chord=0.12,
    cm_quarter_chord=-0.05,
    wetted_surface_ratio=2.05,
    interference_factor=1.0,
    clmax=1.5,
    flap=False
)