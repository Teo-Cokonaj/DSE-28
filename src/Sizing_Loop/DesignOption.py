import aerosandbox as asb
import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import os
import sys

current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(current_file))
sys.path.append(project_root)

from global_parameters import CONSTANTS, Assumptions
import Drag.component_method as dcm
from flight_envelope.flight_envelope import FlightEnvelope
from objects.aircraft_parameters import AircraftParameters
from objects.wing_planform import WingPlanform

class DesignOption():
    def __init__(self, assumptions:Assumptions=Assumptions(), canard:bool=False):
        self.assumptions = assumptions()
        self.flight_envelope = FlightEnvelope()
        self.canard = canard


    def generate_lift_distribution(self, load_factor:float, aircraft_parameters:AircraftParameters, wing_planfom:WingPlanform)->asb.LiftingLine:
        return asb.LiftingLine()

    
    def estimate_CD0(self, aircraft_parameters:AircraftParameters, wing_planfom:WingPlanform):
        pass