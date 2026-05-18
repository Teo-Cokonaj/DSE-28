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
        velocity=30.0
        angle_of_attack_deg=1.0

        lifting_line_theory.wing_planform.sweep_quarter_deg=0.0
        lifting_line_theory.wing_planform.taper=1.0
        lifting_line_theory.initialize_airfoils()

        lifting_line_theory.make_full_airplane_model(main_wing=True,
                                                      canard=False,
                                                      horizontal_stabilizer=False,
                                                      vertical_stabilizer=False)
        
        _,results=lifting_line_theory.run_llt_arbitrary_analysis(altitude_m,
                                                                        velocity,
                                                                        angle_of_attack_deg)
        _,results_zero_aoa=lifting_line_theory.run_llt_arbitrary_analysis(altitude_m,
                                                                        velocity,
                                                                        angle_of_attack_deg=0.0)
        AR=lifting_line_theory.wing_planform.aspect_ratio

        #Prandtl
        reference_lift_curve_slope_per_rad = assumptions.airfoil_C_l_alpha/(1+assumptions.airfoil_C_l_alpha/np.pi/AR)
        numerical_CL_alpha_per_rad=(results["CL"]-results_zero_aoa["CL"])/np.deg2rad(angle_of_attack_deg)
        difference=reference_lift_curve_slope_per_rad-numerical_CL_alpha_per_rad
        relative_difference=abs(difference)/min(reference_lift_curve_slope_per_rad,numerical_CL_alpha_per_rad)
        assert relative_difference<0.200

        altitude_m = 8000.0
        velocity=200.0
        angle_of_attack_deg=1.0

        atmosphere=asb.Atmosphere(altitude_m)
        mach=velocity/atmosphere.speed_of_sound()
        beta=np.sqrt(1-mach**2)
        kappa=assumptions.airfoil_C_l_alpha/(2*np.pi)

        lifting_line_theory.wing_planform.sweep_quarter_deg=45.0
        lifting_line_theory.wing_planform.taper=0.3
        lifting_line_theory.initialize_airfoils()

        lifting_line_theory.make_full_airplane_model(main_wing=True,
                                                      canard=False,
                                                      horizontal_stabilizer=False,
                                                      vertical_stabilizer=False)
        _,results_zero_aoa=lifting_line_theory.run_llt_arbitrary_analysis(altitude_m,
                                                                        velocity,
                                                                        angle_of_attack_deg=0.0)
        
        analysis,results=lifting_line_theory.run_llt_arbitrary_analysis(altitude_m,
                                                                        velocity,
                                                                        angle_of_attack_deg)
        sweep_half_rad = np.arctan(np.tan(wing_planform.sweep_LE_rad-0.5*2*wing_planform.c_root/wing_planform.span*(1-wing_planform.taper)))
        AR=wing_planform.aspect_ratio
        reference_lift_curve_slope_per_rad = 2*np.pi*AR/(2+np.sqrt(4+(AR*beta/kappa)**2*(1+(np.tan(sweep_half_rad))**2/beta**2)))
        numerical_CL_alpha_per_rad=(results["CL"]-results_zero_aoa["CL"])/np.deg2rad(angle_of_attack_deg)
        difference=reference_lift_curve_slope_per_rad-numerical_CL_alpha_per_rad
        relative_difference=abs(difference)/min(reference_lift_curve_slope_per_rad,numerical_CL_alpha_per_rad)
        assert (relative_difference<0.200)
        assert isinstance(results,dict)

    def test_find_aoa_for_trim(self,
                               aircraft_parameters,
                               lifting_line_theory,
                               wing_planform,
                               assumptions):
        altitude_m = 0.0
        velocity=50.0

        lifting_line_theory.initialize_airfoils()

        lifting_line_theory.make_full_airplane_model(main_wing=True,
                                                      canard=False,
                                                      horizontal_stabilizer=False,
                                                      vertical_stabilizer=False)
        computed_aoa_deg=lifting_line_theory.find_aoa_for_force_equilibrium(velocity,
                                                                altitude_m)

        sweep_quarter_rad=wing_planform.sweep_quarter_rad
        AR=wing_planform.aspect_ratio
        atmosphere=asb.Atmosphere(altitude_m)
        mach=velocity/atmosphere.speed_of_sound()
        beta=np.sqrt(1-mach**2)
        kappa=assumptions.airfoil_C_l_alpha/(2*np.pi)
        sweep_half_rad = np.arctan(np.tan(wing_planform.sweep_LE_rad-0.5*2*wing_planform.c_root/wing_planform.span*(1-wing_planform.taper)))
        analytic_lift_curve_slope_per_rad= 2*np.pi*AR/(2+np.sqrt(4+(AR*beta/kappa)**2*(1+(np.tan(sweep_half_rad))**2/beta**2)))
        dynamic_pressure = 0.5 *velocity**2 * 1.225
        required_CL = aircraft_parameters.total_mass * CONSTANTS.G0 / dynamic_pressure / wing_planform.wing_area
        analytic_aoa_deg=np.degrees(required_CL/analytic_lift_curve_slope_per_rad)

        difference = analytic_aoa_deg-computed_aoa_deg

        assert abs(difference)/min(analytic_aoa_deg,computed_aoa_deg)<0.2


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

        assert (abs(difference)/min(analytic_lift_curve_slope_per_rad,computed_lift_curve_slope_per_rad)<0.3)