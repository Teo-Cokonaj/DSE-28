import numpy as np
import os
import sys

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from util.isa_calculator import dens_at_h, speed_of_sound_at_h, viscosity_at_h

class Component:
    def __init__(self, interference_factor:float, surface_wetted:float, 
                 characteristic_length:float, laminar_fraction:float, surface_reynolds_factor:float=.405e-5):
        self.interfereance_factor = interference_factor
        self.surface_wetted = surface_wetted
        self.characteristic_length = characteristic_length
        self.laminar_fraction = laminar_fraction
        self.surface_reynolds_factor = surface_reynolds_factor
    

    def Cf(self, altitude:float, mach:float):
        reynolds_ = self.reynolds(altitude, mach)
        laminar_comp = self.laminar_fraction*1.328/np.sqrt(reynolds_)
        turbulent_comp = (1-self.laminar_fraction)*.455/(np.log10(reynolds_)**2.58*(1+.144*mach**2)**.65)
        return laminar_comp + turbulent_comp


    def reynolds(self, altitude:float, mach:float):
        density = dens_at_h(altitude)
        speed_of_sound = speed_of_sound_at_h(altitude)
        viscosity = viscosity_at_h(altitude)
        
        return min(density*speed_of_sound*mach*self.characteristic_length/viscosity,
            38.21*(self.characteristic_length/self.surface_reynolds_factor) ** 1.053)


    def form_factor(self, mach:float):
        raise NotImplementedError
    

    def CD_comp(self, altitude:float, mach:float):
        return self.Cf(altitude, mach) * self.form_factor(mach) * self.interfereance_factor * self.surface_wetted