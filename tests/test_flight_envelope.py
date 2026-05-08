import pytest
import aerosandbox.numpy as np
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.global_parameters import CONSTANTS, Assumptions
from src.objects.aircraft_parameters import AircraftParameters
from src.objects.wing_planform import WingPlanform
from src.flight_envelope.flight_envelope import FlightEnvelope


@pytest.fixture
def aircraft_parameters():
    return AircraftParameters(total_mass=7.0660)


@pytest.fixture
def wing_planform():
    wing = WingPlanform(
        aspect_ratio=8.0,
        span=2.8,
        sweep_quarter_deg=0.0,
        taper=1.0,
    )
    return wing


@pytest.fixture
def constants():
    return CONSTANTS()


@pytest.fixture
def assumptions():
    assumptions = Assumptions()
    assumptions.ALTITUDE_CRUISE = 0.0
    assumptions.AIR_DENSITY_CRUISE_ALTITUDE = 1.225
    assumptions.positive_C_L_max = 1.6
    assumptions.negative_C_L_max = -0.8
    assumptions.C_L_alpha = 1.5464
    assumptions.MC=0.5 #cruise Mach number
    assumptions.MD = 0.6 #ADSEE: in general, MD is 0.05M higher than MC
    return assumptions


@pytest.fixture
def flight_envelope(constants,
                    assumptions,
                    aircraft_parameters,
                    wing_planform):
    fe = FlightEnvelope(constants, assumptions)

    fe.positive_manoeuvring_limit_load_factor = 3.8
    fe.negative_manoeuvring_limit_load_factor = (
        -0.5 * fe.positive_manoeuvring_limit_load_factor
    )

    fe.compute_design_speeds(aircraft_parameters,
                                     wing_planform,
                                     assumptions)

    fe.design_cruising_speed = 20.20
    fe.design_diving_speed = 28.28
    return fe


class TestFlightEnvelope:
    def test_kts_conversion(self,
                            flight_envelope):
        assert np.isclose(1.0*0.51444444,flight_envelope.kts_to_mps(1.0))
    
    def test_fps_conversion(self,
                            flight_envelope):
        assert np.isclose(1.0*0.3048,flight_envelope.fps_to_mps(1.0))

    def test_stall_speed(self,
                         flight_envelope,
                         aircraft_parameters,
                         wing_planform,
                         assumptions):
        actual_stall_speed=np.sqrt(2*aircraft_parameters.total_mass*CONSTANTS.G0/(CONSTANTS.AIR_DENSITY_SEA_LEVEL*wing_planform.wing_area*assumptions.positive_C_L_max))
        assert np.isclose(actual_stall_speed,flight_envelope.V_stall(aircraft_parameters,wing_planform,assumptions.positive_C_L_max))

    def test_minimum_design_cruising_speed(self,
                                           flight_envelope,
                                           aircraft_parameters,
                                           wing_planform):
        assert np.isclose(2.4*np.sqrt(aircraft_parameters.total_mass*CONSTANTS.G0/wing_planform.wing_area),
                          flight_envelope.minimum_cruising_speed)
        
    
    def test_upper_manoeuvre_load_curve(self,
                                        wing_planform,
                                        aircraft_parameters,
                                        assumptions,
                                        flight_envelope,):
        assert np.isclose(0.5*CONSTANTS.AIR_DENSITY_SEA_LEVEL*wing_planform.wing_area*assumptions.positive_C_L_max/(aircraft_parameters.total_mass*CONSTANTS.G0),
                          flight_envelope.load_factor_upper_manoeuvre_curve(1.0,
                                          wing_planform,
                                          aircraft_parameters,
                                          assumptions))
        

    def test_lower_manoeuvre_load_curve(self,
                                        wing_planform,
                                        aircraft_parameters,
                                        assumptions,
                                        flight_envelope,):
                assert np.isclose(0.5*CONSTANTS.AIR_DENSITY_SEA_LEVEL*wing_planform.wing_area*assumptions.negative_C_L_max/(aircraft_parameters.total_mass*CONSTANTS.G0),
                          flight_envelope.load_factor_lower_manoeuvre_curve(1.0,
                                          wing_planform,
                                          aircraft_parameters,
                                          assumptions))

    def test_delta_load_factor_gust(self,
                                    assumptions,
                                    wing_planform,
                                    aircraft_parameters,
                                    flight_envelope):
        
        assumptions.ALTITUDE_CRUISE=5000.0 #m
        assumptions.AIR_DENSITY_CRUISE_ALTITUDE=0.7362 #kg/m^3

        mu_g=(2*aircraft_parameters.total_mass)/(assumptions.AIR_DENSITY_CRUISE_ALTITUDE*wing_planform.MAC*assumptions.C_L_alpha*wing_planform.wing_area)
        K_g=(0.88*mu_g)/(5.3+mu_g)

        derived_gust_velocity=flight_envelope.fps_to_mps(50.0)  #this function verified already   
        assert np.isclose(K_g*CONSTANTS.AIR_DENSITY_SEA_LEVEL*derived_gust_velocity*1.0*assumptions.C_L_alpha/(2*aircraft_parameters.total_mass*CONSTANTS.G0/wing_planform.wing_area),
                                  flight_envelope.delta_load_factor_gust_curve(1.0,
                                                     wing_planform,
                                                     aircraft_parameters,
                                                     assumptions,
                                                     condition='cruise'))

        derived_gust_velocity=flight_envelope.fps_to_mps(25.0)     #this function verified already 
        assert np.isclose(K_g*CONSTANTS.AIR_DENSITY_SEA_LEVEL*derived_gust_velocity*1.0*assumptions.C_L_alpha/(2*aircraft_parameters.total_mass*CONSTANTS.G0/wing_planform.wing_area),
                                  flight_envelope.delta_load_factor_gust_curve(1.0,
                                                     wing_planform,
                                                     aircraft_parameters,
                                                     assumptions,
                                                     condition='dive'))
        
        assumptions.ALTITUDE_CRUISE=15000.0
        assumptions.AIR_DENSITY_CRUISE_ALTITUDE=0.1938 #kg/m^3

        mu_g=(2*aircraft_parameters.total_mass)/(assumptions.AIR_DENSITY_CRUISE_ALTITUDE*wing_planform.MAC*assumptions.C_L_alpha*wing_planform.wing_area)
        K_g=(0.88*mu_g)/(5.3+mu_g)

        derived_gust_velocity=flight_envelope.fps_to_mps(50.0+(25.0-50.0)/(15240.0-6096.0)*(assumptions.ALTITUDE_CRUISE-6096.0))  #this function verified already 
        assert np.isclose(K_g*CONSTANTS.AIR_DENSITY_SEA_LEVEL*derived_gust_velocity*1.0*assumptions.C_L_alpha/(2*aircraft_parameters.total_mass*CONSTANTS.G0/wing_planform.wing_area),
                                  flight_envelope.delta_load_factor_gust_curve(1.0,
                                                     wing_planform,
                                                     aircraft_parameters,
                                                     assumptions,
                                                     condition='cruise'))
        

        derived_gust_velocity=flight_envelope.fps_to_mps(25.0+(12.5-25.0)/(15240.0-6096.0)*(assumptions.ALTITUDE_CRUISE-6096.0))
        assert np.isclose(K_g*CONSTANTS.AIR_DENSITY_SEA_LEVEL*derived_gust_velocity*1.0*assumptions.C_L_alpha/(2*aircraft_parameters.total_mass*CONSTANTS.G0/wing_planform.wing_area),
                                  flight_envelope.delta_load_factor_gust_curve(1.0,
                                                     wing_planform,
                                                     aircraft_parameters,
                                                     assumptions,
                                                     condition='dive'))

    def test_plot_diagram(self,
                          assumptions,
                          wing_planform,
                          aircraft_parameters,
                          flight_envelope):
        
        print('Inspect the plot!')
        flight_envelope.plot_V_n_diagram(aircraft_parameters,
                                         wing_planform,
                                         assumptions)

