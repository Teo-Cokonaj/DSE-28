'''
The objective of this testing file is to ensure that modifications to 
the source code of Aerosandbox do not affect the computation
of the lift coefficient.
'''

import pytest
import aerosandbox as asb
import aerosandbox.numpy as np
import numpy.testing as nte
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.global_parameters import CONSTANTS, Assumptions
from src.objects.aircraft_parameters import AircraftParameters
from src.objects.lifting_surface_planform import LiftingSurfacePlanform
from src.flight_envelope.flight_envelope import FlightEnvelope
from src.aerodynamic_model.lifting_line_theory import LiftingLineTheory
from airfoil.SymmetricAirfoil import SymmetricAirfoil
from aerodynamic_model.lifting_line_inviscid import LiftingLineInviscid
from typing_extensions import assert_type


@pytest.fixture
def aircraft_parameters():
    return AircraftParameters(total_mass=50.0,
                        horizontal_stabilizer_distance_from_wing=3.0,
                        vertical_stabilizer_distance_from_wing=3.0,
                        canard_distance_in_front_of_wing=0.5)


@pytest.fixture
def wing_planform():
    return LiftingSurfacePlanform(aspect_ratio=25.0,
                                span=2.0,
                                sweep_quarter_deg=0.0,
                                taper=1.0,
                                tip_twist_rad=0.0)

@pytest.fixture
def horizontal_stabilizer_planform():
     return LiftingSurfacePlanform(aspect_ratio=3.0,
                                                                span=0.5,
                                                                sweep_quarter_deg=45.0,
                                                                taper=1.0,
                                                                tip_twist_rad=0.0)

@pytest.fixture
def vertical_stabilizer_planform():
     return LiftingSurfacePlanform(aspect_ratio=3.0,
                                                                span=0.3,
                                                                sweep_quarter_deg=0.0,
                                                                taper=0.3,
                                                                tip_twist_rad=0.0)

@pytest.fixture
def canard_planform():
     return LiftingSurfacePlanform(aspect_ratio=3.0,
                                                                span=0.3,
                                                                sweep_quarter_deg=45.0,
                                                                taper=1.0,
                                                                tip_twist_rad=0.0)

@pytest.fixture
def lifting_line_theory(aircraft_parameters,
                        wing_planform,
                        horizontal_stabilizer_planform,
                        vertical_stabilizer_planform):

     return LiftingLineTheory(aircraft_parameters,
                            wing_planform,
                            horizontal_stabilizer_planform,
                            vertical_stabilizer_planform,
                                          )
                    

@pytest.fixture
def constants():
    return CONSTANTS()


@pytest.fixture
def assumptions():
    return Assumptions()


class TestInviscidAnalysis:
    
    def test_run_llt_arbitrary_analysis(self,
                                lifting_line_theory,
                                wing_planform,
                                assumptions):
        altitude_m = 0
        velocity=30.0
        atmosphere=asb.Atmosphere(altitude_m)
        angle_of_attack_deg=1.0

        lifting_line_theory.wing_planform.sweep_quarter_deg=0.0
        lifting_line_theory.wing_planform.taper=1.0
        lifting_line_theory.initialize_airfoils()

        lifting_line_theory.make_full_airplane_model(main_wing=True,
                                                      canard=False,
                                                      horizontal_stabilizer=False,
                                                      vertical_stabilizer=False)
        
        op_point = asb.OperatingPoint(
                atmosphere=asb.Atmosphere(altitude_m),
                velocity=velocity,
                alpha=angle_of_attack_deg,
                beta=0,
                p=0,
                q=0,
                r=0,
            )

        def linear_spacing(start,end,number_of_stations):
            return np.linspace(0,1,number_of_stations)
        
        _,inviscid_results=lifting_line_theory.run_llt_arbitrary_analysis(altitude_m,
                                                        velocity,
                                                        angle_of_attack_deg)

        viscous_analysis = asb.LiftingLine(
                airplane=lifting_line_theory.airplane,
                op_point=op_point,
                spanwise_spacing_function=linear_spacing,
            )
        viscous_results = viscous_analysis.run()
  

        difference=abs(inviscid_results["CL"]-viscous_results["CL"])
        relative_difference=abs(difference)/min(inviscid_results["CL"],viscous_results["CL"])
        assert relative_difference<0.01


  