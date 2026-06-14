import sys
import os
import numpy as np
import aerosandbox as asb
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src_final.Requirements.Requirement import Requirement
from Aircraft.Aircraft import Aircraft
from Aircraft.Planform import Planform
from Aircraft.Fixed import Fixed
from MatchingDiagram.MatchingDiagramJet import MatchingDiagramJet
from src_final.global_parameters import CONSTANTS, Assumptions


class MDReq(Requirement):
    def __init__(self, matching_diagram:MatchingDiagramJet=MatchingDiagramJet(2), assumptions:Assumptions=Assumptions(), mtom=50.):
        self.assumptions = assumptions
        self.matching_diagram = matching_diagram
        self.mtom = mtom


    def assess(self, 
               aircraft:Aircraft) -> bool:
        
        fixed = aircraft.fixed
        planform = aircraft.planforms[0]
        
        self.matching_diagram.add_landing_field_length(
            constraint_label = "Landing Length", 
            field_length = self.assumptions.airfield_length, 
            CL_max = planform.positive_C_L_max 
            )

        self.matching_diagram.add_cruise_speed(
            constraint_label = "Mach max", 
            mach = self.assumptions.mach_max, 
            CD0 = aircraft.CD0_mach_max,
            inviscid_ratio = planform.inviscid_ratio,
            atmosphere = asb.Atmosphere(self.assumptions.altitude_mach_max),
            beta = (1 - (fixed.fuel_mass / aircraft.total_mass()) / 2) #NOTE: we must be able to perform mach max half-fuelled
        )
        
        self.matching_diagram.add_cruise_speed(
            constraint_label = "Cruise speed",
            mach = self.assumptions.mach_cruise,
            CD0 = aircraft.CD0_cruise,
            inviscid_ratio = planform.inviscid_ratio,
            atmosphere = asb.Atmosphere(self.assumptions.altitude_mach_max)
        )

        self.matching_diagram.add_climb_gradient(
            constraint_label = "Climb gradient AEO",
            tan_gradient = CONSTANTS.CLIMB_GRADIENT_AEO,
            CD0 = aircraft.CD0_takeoff,
            inviscid_ratio = planform.inviscid_ratio,
            all_engines_operative = True,
            atmosphere = asb.Atmosphere(0.)
        )
        
        self.matching_diagram.add_climb_gradient(
            constraint_label = "Climb gradient OEI",
            tan_gradient = CONSTANTS.CLIMB_GRADIENT_OEI,
            CD0 = aircraft.CD0_go_around,
            inviscid_ratio = planform.inviscid_ratio,
            all_engines_operative = False,
            atmosphere = asb.Atmosphere(CONSTANTS.ALTITUDE_OEI_CLIMB)
        )
        #NOTE: there is also a 3% climb gradient on balked landing in the landing configuration, but since our Toff and landing configs are same (no HLDs), we skip that one

        self.matching_diagram.add_takeoff_field_length(
            constraint_label = "Takeoff length", 
            field_length = self.assumptions.airfield_length,
            inviscid_ratio = planform.inviscid_ratio,
            CL_takeoff = planform.positive_C_L_max 
        )
        
        wing_loading = self.mtom*CONSTANTS.G0/aircraft.planforms[0].wing_area#aircraft.wing_loading()
        thrust_to_weight = aircraft.thrust_to_weight()

        # self.matching_diagram.create_wing_loading_axis()
        # self.matching_diagram.plot(wing_loading, thrust_to_weight, max_thrust_weight=1.0)
        
        results = {}

        for label, ws_constraint in self.matching_diagram.constraints_wing_loading.items():
            results[label] = bool(wing_loading <= ws_constraint)

        for label, tw_constraint in self.matching_diagram.constraints_thrust_weight.items():
            results[label] = bool(thrust_to_weight >= tw_constraint(wing_loading))

        return not (False in results.values())
        
        
    
        
        
