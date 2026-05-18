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


class TestAerodynamicModel:
    def test_LE_positions(self,
                          lifting_line_theory,
                            wing_planform):
        nte.assert_allclose(lifting_line_theory.calculate_LE_x_positions(lifting_line_theory.wing_number_of_sections,
                                                                                       wing_planform),
                                          np.linspace(0.0,
                                                      wing_planform.half_span*np.tan(wing_planform.sweep_LE_rad),
                                                        lifting_line_theory.wing_number_of_sections))

    def test_section_y_positions(self,
                          lifting_line_theory,
                            wing_planform):
        nte.assert_allclose(lifting_line_theory.calculate_section_y_positions(lifting_line_theory.wing_number_of_sections,
                                                                                       wing_planform),
                                          np.linspace(0.0,wing_planform.half_span,
                                                      lifting_line_theory.wing_number_of_sections))
    
    def test_run_llt_arbitrary_analysis(self,
                                lifting_line_theory,
                                wing_planform,
                                assumptions):
        altitude_m = 0
        velocity=50.0
        angle_of_attack_deg=7.0
        lifting_line_theory.initialize_airfoils()
        #Make a wing model
        lifting_line_theory.make_full_airplane_model(main_wing=True,
                                                      canard=False,
                                                      horizontal_stabilizer=False,
                                                      vertical_stabilizer=False)
        
        analysis,results=lifting_line_theory.run_llt_arbitrary_analysis(altitude_m,
                                                                        velocity,
                                                                        angle_of_attack_deg)
        #Kuchemann
        sweep_quarter_rad=wing_planform.sweep_quarter_rad
        AR=wing_planform.aspect_ratio
        reference_lift_curve_slope_per_rad= 2*np.pi*np.cos(sweep_quarter_rad)/(np.sqrt(1+(2*np.pi*np.cos(sweep_quarter_rad)/np.pi/AR)**2)+2*np.pi*np.cos(sweep_quarter_rad)/np.pi/AR)

        analytic_CL=reference_lift_curve_slope_per_rad*np.deg2rad(angle_of_attack_deg)
        numerical_CL=results["CL"]
        difference=analytic_CL-numerical_CL

        assert (abs(difference)/min(analytic_CL,numerical_CL)<0.1)
        assert isinstance(analysis, LiftingLineInviscid)
        assert isinstance(results,dict)

    def test_find_aoa_for_trim(self,
                               aircraft_parameters,
                               lifting_line_theory,
                               wing_planform):
        altitude_m = 0.0
        velocity=50.0

        lifting_line_theory.initialize_airfoils()
        #Make a wing model
        lifting_line_theory.make_full_airplane_model(main_wing=True,
                                                      canard=False,
                                                      horizontal_stabilizer=False,
                                                      vertical_stabilizer=False)
        computed_aoa_deg=lifting_line_theory.find_aoa_for_force_equilibrium(velocity,
                                                                altitude_m)
        #Kuchemann
        sweep_quarter_rad=wing_planform.sweep_quarter_rad
        AR=wing_planform.aspect_ratio
        analytic_lift_curve_slope_per_rad= 2*np.pi*np.cos(sweep_quarter_rad)/(np.sqrt(1+(2*np.pi*np.cos(sweep_quarter_rad)/np.pi/AR)**2)+2*np.pi*np.cos(sweep_quarter_rad)/np.pi/AR)

        dynamic_pressure = 0.5 *velocity**2 * 1.225
        required_CL = aircraft_parameters.total_mass * CONSTANTS.G0 / dynamic_pressure / wing_planform.wing_area
        analytic_aoa_deg=np.degrees(required_CL/analytic_lift_curve_slope_per_rad)

        difference = analytic_aoa_deg-computed_aoa_deg

        assert abs(difference)/min(analytic_aoa_deg,computed_aoa_deg)<0.1


    def test_llt_alpha_sweep_analysis(self,
                                aircraft_parameters,
                               lifting_line_theory,
                               wing_planform):
        #Test lift curve slope
        altitude_m = 0.0
        velocity=50.0

        lifting_line_theory.initialize_airfoils()
        #Make a wing model
        lifting_line_theory.make_full_airplane_model(main_wing=True,
                                                      canard=False,
                                                      horizontal_stabilizer=False,
                                                      vertical_stabilizer=False)
        results=lifting_line_theory.run_llt_alpha_sweep(velocity,
                                                                altitude_m)
        
        computed_lift_curve_slope_per_rad=results["lift_curve_slope_per_rad"]
        #Kuchemann
        sweep_quarter_rad=wing_planform.sweep_quarter_rad
        AR=wing_planform.aspect_ratio
        analytic_lift_curve_slope_per_rad= 2*np.pi*np.cos(sweep_quarter_rad)/(np.sqrt(1+(2*np.pi*np.cos(sweep_quarter_rad)/np.pi/AR)**2)+2*np.pi*np.cos(sweep_quarter_rad)/np.pi/AR)
        difference=analytic_lift_curve_slope_per_rad-computed_lift_curve_slope_per_rad

        assert (abs(difference)/min(analytic_lift_curve_slope_per_rad,computed_lift_curve_slope_per_rad)<0.1)

        print('Position of aerodynamic centre: ',results['x_ac'])
        #Test aerodynamic centre position