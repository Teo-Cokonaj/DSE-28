import pytest
import aerosandbox as asb
import aerosandbox.numpy as np
import numpy.testing as nte
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src_final.global_parameters import CONSTANTS, Assumptions
from src_final.Aircraft.Planform import Planform

@pytest.fixture
def planform():
    return  Planform(aspect_ratio=20.0,
    span=2.0,
    sweep_quarter_deg=0.0,
    taper=1.0,
    thickness_to_chord=0.12,
    cm_quarter_chord=1.0,
    wetted_surface_ratio=1.0,
    interference_factor=1.0,
    clmax=1.5,
    flap=False,)
                    

@pytest.fixture
def constants():
    return CONSTANTS()


@pytest.fixture
def assumptions():
    return Assumptions()


class TestPlanformLift:
    def test_LE_positions(self,
                          planform,
                          assumptions):
        number_of_stations=100
        reference_stall_speed=np.sqrt(assumptions.positive_manoeuvring_limit_load_factor*assumptions.initial_total_aircraft_mass*CONSTANTS.G0/(0.5*CONSTANTS.AIR_DENSITY_SEA_LEVEL*planform.wing_area*planform.positive_C_L_max))
        sectional_chords, _, sectional_spanwise_positions,_ = planform.sectional_properties(number_of_stations)
        sectional_chords, _, sectional_spanwise_positions,_=sectional_chords[1:], _,sectional_spanwise_positions[1:],_
        full_dy = np.diff(np.linspace(0, planform.half_span, number_of_stations))
        index_closest_to_fuselage=np.argmin(np.abs(sectional_spanwise_positions - assumptions.diameter_fuselage/2))

        easa_chord = 0.5*(sectional_chords+4/np.pi*planform.MAC*np.sqrt(1-((sectional_spanwise_positions-assumptions.diameter_fuselage/2)/(sectional_spanwise_positions[-1]-assumptions.diameter_fuselage/2))**2))
        full_sectional_lifts_schenk = 0.5*CONSTANTS.AIR_DENSITY_SEA_LEVEL*reference_stall_speed**2*planform.positive_C_L_max*easa_chord*full_dy
        reduced_sectional_lifts_schrenk = full_sectional_lifts_schenk[index_closest_to_fuselage:]
        reduced_sectional_spanwise_positions=sectional_spanwise_positions[index_closest_to_fuselage:]
        modified_sectional_lifts_schrenk=(np.sum(full_sectional_lifts_schenk)/np.sum(reduced_sectional_lifts_schrenk))*reduced_sectional_lifts_schrenk

        numerical_results=planform.estimate_conservative_lift_distribution(
                                                diameter_fuselage=assumptions.diameter_fuselage,
                                                positive_manoeuvring_limit_load_factor=assumptions.positive_manoeuvring_limit_load_factor,
                                                initial_total_aircraft_mass=assumptions.initial_total_aircraft_mass,
                                                number_of_stations=number_of_stations,
                                                )
        nte.assert_allclose(numerical_results[0],reduced_sectional_spanwise_positions)
        nte.assert_allclose(numerical_results[1], modified_sectional_lifts_schrenk)
