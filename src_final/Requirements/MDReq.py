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
    def assess(self, 
               aircraft:Aircraft, 
               planform:Planform, 
               fixed:Fixed, 
               matching_diagram:MatchingDiagramJet, 
               assumptions:Assumptions) -> bool:
        
        landing_constraint = matching_diagram.add_landing_field_length(
            constraint_label = "Landing Length", 
            field_length = assumptions.airfield_length, 
            CL_max = aircraft.cl_max() # placeholder function
            )

        cruise_constraint_halfFuelled = matching_diagram.add_cruise_speed(
            constraint_label = "Mach max", 
            mach = assumptions.mach_max, 
            CD0 = 0,
            inviscid_ratio = planform.inviscid_ratio,
            atmosphere = asb.Atmosphere(assumptions.altitude_mach_max),
            beta = (1 - (fixed.fuel_mass / aircraft.total_mass()) / 2) #NOTE: we must be able to perform mach max half-fuelled
        )
        
        cruise_constraint = matching_diagram.add_cruise_speed(
            constraint_label = "Cruise speed",
            mach = CONSTANTS.MACH_CRUISE,
            CD0 = 0,
            inviscid_ratio = planform.inviscid_ratio,
            atmosphere = asb.Atmosphere(assumptions.altitude_mach_max)
        )

        climb_constraint_AEO = matching_diagram.add_climb_gradient(
            constraint_label = "Climb gradient AEO",
            tan_gradient = CONSTANTS.CLIMB_GRADIENT_AEO,
            CD0 = 0,
            inviscid_ratio = planform.inviscid_ratio,
            all_engines_operative = True,
            atmosphere = asb.Atmosphere(0.)
        )
        
        climb_constraint_OEI = matching_diagram.add_climb_gradient(
            constraint_label = "Climb gradient OEI",
            tan_gradient = CONSTANTS.CLIMB_GRADIENT_OEI,
            CD0 = 0,
            inviscid_ratio = planform.inviscid_ratio,
            all_engines_operative = False,
            atmosphere = asb.Atmosphere(CONSTANTS.ALTITUDE_OEI_CLIMB)
        )
        #NOTE: there is also a 3% climb gradient on balked landing in the landing configuration, but since our Toff and landing configs are same (no HLDs), we skip that one

        TO_constraint = matching_diagram.add_takeoff_field_length(
            constraint_label = "Takeoff length", 
            field_length = assumptions.airfield_length,
            inviscid_ratio = planform.inviscid_ratio,
            CL_max = aircraft.cl_max() # placeholder function
        )
        
        wing_loading = aircraft.wing_loading()
        
        
    
        
        
