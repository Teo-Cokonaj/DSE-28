import pytest as pt
import numpy as np

from src.Class_I.fuel_mass_fraction import fuel_mass_fraction
from src.global_parameters import CONSTANTS

class TestFuelMassFraction:
    debug = False

    single_glide_ratio = 10.
    altitude_go_around = 2000. # [m]
    altitude_cruise = 5000. # [m]
    CL_go_around = .6
    wing_loading = 3000 # [Pa]
    efficiency_engine_total = .87
    enegy_density_saf = 42.8e6 # [J/kg]
    airspeed_approach = 60. # [m/s]

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

        computed_fuel_fraction = fuel_mass_fraction(self.altitude_go_around, self.altitude_cruise, self.time_half_turn, self.CL_go_around, self.single_glide_ratio, self.single_glide_ratio, 
                                                    self.single_glide_ratio, self.airspeed_approach, self.wing_loading, self.efficiency_engine_total, self.enegy_density_saf, self.debug)
        
        if self.debug:
            print("====REFERENCE====")
            print(f"load_factor_go_around: {self.load_factor_go_around}")
            print(f"load_factor_go_around: {self.airspeed_go_around}")
            print(f"equivalent range: {range_equivalent}")

        assert np.isclose(reference_fuel_fraction, computed_fuel_fraction), f"computed: {computed_fuel_fraction}, reference: {reference_fuel_fraction}"