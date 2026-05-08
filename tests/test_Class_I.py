import pytest as pt
import numpy as np
import sys
import os

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Class_I.Class_I import Class_I
from src.global_parameters import CONSTANTS

class TestClass_I:
    debug = False

    single_glide_ratio = 10.
    altitude_go_around = 2000. # [m]
    altitude_cruise = 5000. # [m]
    CL_go_around = .6
    wing_loading = 3000 # [Pa]
    efficiency_engine_total = .87
    enegy_density_saf = 42.8e6 # [J/kg]
    airspeed_approach = 60. # [m/s]
    oem_fraction = .4

    #rate I turn @ go around
    time_half_turn = 60. # [s]
    omega_turn = np.pi/60. # [rad/s]

    temperature_cruise = CONSTANTS.TEMPERATURE_SEA_LEVEL+CONSTANTS.TEMPERATURE_LAPSE*altitude_cruise
    speed_of_sound_cruise = np.sqrt(CONSTANTS.GAMMA_AIR*CONSTANTS.GAS_CONSTANT_AIR*temperature_cruise)
    temperature_mach_max = CONSTANTS.TEMPERATURE_SEA_LEVEL+CONSTANTS.TEMPERATURE_LAPSE*CONSTANTS.ALTITUDE_MACH_MAX
    speed_of_sound_mach_max = np.sqrt(CONSTANTS.GAMMA_AIR*CONSTANTS.GAS_CONSTANT_AIR*temperature_mach_max)
    temperature_go_around = CONSTANTS.TEMPERATURE_SEA_LEVEL+CONSTANTS.TEMPERATURE_LAPSE*altitude_go_around
    pressure_go_around = CONSTANTS.PRESSURE_SEA_LEVEL*(temperature_go_around/CONSTANTS.TEMPERATURE_SEA_LEVEL)**(-CONSTANTS.G0/CONSTANTS.GAS_CONSTANT_AIR/CONSTANTS.TEMPERATURE_LAPSE)
    density_go_around = pressure_go_around/CONSTANTS.GAS_CONSTANT_AIR/temperature_go_around

    load_factor_quadratic_term = wing_loading*2/density_go_around/CL_go_around*(omega_turn/CONSTANTS.G0)**2
    load_factor_go_around = (load_factor_quadratic_term+np.sqrt(load_factor_quadratic_term**2+4))/2
    airspeed_go_around = np.sqrt(wing_loading*2/density_go_around*load_factor_go_around/CL_go_around)

    def test_single_glide_ratio(self):
        range_nominal = (CONSTANTS.MACH_CRUISE*self.speed_of_sound_cruise*CONSTANTS.TIME_CRUISE 
                        +CONSTANTS.MACH_MAX*self.speed_of_sound_mach_max*CONSTANTS.TIME_MACH_MAX 
                        +CONSTANTS.N_LANDING_ATTEMPTS*self.airspeed_go_around*self.time_half_turn)
        range_lost = 1/.7*self.single_glide_ratio*(CONSTANTS.ALTITUDE_MACH_MAX+(CONSTANTS.MACH_MAX*self.speed_of_sound_mach_max)**2/2/CONSTANTS.G0
                                                   +CONSTANTS.N_LANDING_ATTEMPTS*(self.altitude_go_around+(self.airspeed_go_around**2-self.airspeed_approach**2)/2/CONSTANTS.G0))
        range_equivalent = range_nominal + range_lost

        reference_fuel_fraction = 1-np.exp(-(range_equivalent)*CONSTANTS.G0/self.efficiency_engine_total/self.enegy_density_saf/self.single_glide_ratio)

        reference_payload_fraction = 1 - reference_fuel_fraction - self.oem_fraction
        reference_fuel_mass = CONSTANTS.MASS_PAYLOAD*reference_fuel_fraction/reference_payload_fraction
        reference_empty_mass = CONSTANTS.MASS_PAYLOAD*self.oem_fraction/reference_payload_fraction
        reference_mtom = CONSTANTS.MASS_PAYLOAD/reference_payload_fraction

        class_I = Class_I(self.altitude_cruise, self.altitude_go_around, self.efficiency_engine_total, self.enegy_density_saf, self.time_half_turn, self.debug)
        class_I_result = class_I.run_estimation(self.oem_fraction, self.CL_go_around, self.single_glide_ratio, self.single_glide_ratio, self.single_glide_ratio, self.airspeed_approach, self.wing_loading)
        
        if self.debug:
            print("====REFERENCE====")
            print(f"load_factor_go_around: {self.load_factor_go_around}")
            print(f"load_factor_go_around: {self.airspeed_go_around}")
            print(f"equivalent range: {range_equivalent}")

        assert np.isclose(reference_fuel_fraction, class_I_result.fuel_fraction), f"computed: {class_I_result.fuel_fraction}, reference: {reference_fuel_fraction}"
        assert np.isclose(self.oem_fraction, class_I_result.oem_fraction), f"computed: {class_I_result.oem_fraction}, reference: {self.oem_fraction}"
        assert np.isclose(reference_mtom, class_I_result.mtom), f"computed: {class_I_result.mtom}, reference: {reference_mtom}"
        assert np.isclose(reference_payload_fraction, class_I_result.payload_fraction), f"computed: {class_I_result.payload_fraction}, reference: {reference_payload_fraction}"
        assert np.isclose(reference_empty_mass, class_I_result.oem_mass), f"computed: {class_I_result.oem_mass}, reference:{reference_empty_mass}"
        assert np.isclose(reference_fuel_mass, class_I_result.fuel_mass), f"computed: {class_I_result.fuel_mass}, reference:{reference_fuel_mass}"