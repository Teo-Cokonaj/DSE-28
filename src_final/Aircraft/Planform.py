import sys
import os
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Drag.Component import Component

class Planform(Component):
    def __init__(self,
                 aspect_ratio: float,
                 span: float, 
                 sweep_quarter_deg: float,
                 taper: float,
                 thickness_to_chord:float,
                 cm_quarter_chord:float,
                 wetted_surface_ratio:float,
                 interference_factor:float,
                 clmax:float,
                 flap:bool,
                 airfoil_lift_slope:float=np.pi*2,
                 cl0:float=0.,
                 laminar_fraction:float=.05,
                 chord_fraction_maximum_thickness:float = .3,
                 pos_max_camber:float = np.inf
                 ):

        self.thickness_to_chord = thickness_to_chord
        self.cm_quarter_chord = cm_quarter_chord
        self.airfoil_lift_slope = airfoil_lift_slope
        self.cl_0 = cl0
        self.clmax = clmax
        self.flap = flap
        self.aspect_ratio = aspect_ratio
        self.sweep_quarter_rad = np.radians(sweep_quarter_deg)
        self.taper = taper
        self.wing_area = span**2/aspect_ratio

        self.chord_fraction_maximum_thickness = chord_fraction_maximum_thickness
        self.pos_max_camber = pos_max_camber
        self.weight_cache = dict()

        self.oswald = 4.61*(1 - 0.45 * self.aspect_ratio**.68)*np.cos(self.sweep_LE_rad)**0.15 - 3.1

        super().__init__(
            interference_factor = interference_factor, #high wing
            surface_wetted = 2 * wetted_surface_ratio * self.wing_area,
            characteristic_length = self.MAC,
            laminar_fraction = laminar_fraction 
        )


    @property
    def span(self)->float:
        return np.sqrt(self.wing_area * self.aspect_ratio)
    

    @property
    def half_span(self)->float:
        return self.span/2
    

    @property
    def c_root(self)->float:
       return 2*self.wing_area/(self.span*(1+self.taper)) 
        

    @property
    def c_tip(self)->float:
        return self.taper*self.c_root
    

    @property
    def sweep_LE_rad(self)->float:
        return np.arctan(np.tan(self.sweep_quarter_rad) + self.c_root / self.span / 2 * (1 - self.taper))
    

    @property
    def MAC(self)->float:
        return 2/3 * self.c_root * ((1 + self.taper + self.taper**2) / (1 + self.taper))
    

    @property
    def y_MAC(self)->float:
        return self.half_span/3*((1+2*self.taper)/(1+self.taper))
    

    @property
    def x_MAC(self)->float:
        return self.y_MAC*np.tan(self.sweep_LE_rad)
    
    def sectional_areas(self,
                        number_of_sections)->np.ndarray:
        
        y_stations = np.linspace(0, self.half_span, number_of_sections)
    
        c_stations = self.c_root + (self.c_tip - self.c_root) * y_stations / self.half_span
        
        dy = np.diff(y_stations)
        c_inner = c_stations[:-1]
        c_outer = c_stations[1:]
        
        return 0.5 * (c_inner + c_outer) * dy
    
    def aerodynamic_center(self,
                       number_of_sections: int,
                       chord_fraction: float = 0.25) -> float:

        y_stations = np.linspace(0, self.half_span, number_of_sections)
        c_stations = self.c_root + (self.c_tip - self.c_root) * y_stations / self.half_span
        x_le_stations = y_stations * np.tan(self.sweep_LE_rad)

        sectional_areas = self.sectional_areas(number_of_sections)  # length: number_of_sections - 1
        sectional_ACs = []

        for i in range(number_of_sections - 1):
            c_inner = c_stations[i]
            c_outer = c_stations[i + 1]

            xyz_le_inner = np.array([x_le_stations[i],     y_stations[i],     0.0])
            xyz_le_outer = np.array([x_le_stations[i + 1], y_stations[i + 1], 0.0])

            section_taper_ratio = c_outer / c_inner

            section_MAC_length = (
                (2 / 3)
                * c_inner
                * (1 + section_taper_ratio + section_taper_ratio**2)
                / (1 + section_taper_ratio)
            )

            section_MAC_le = xyz_le_inner + (
                xyz_le_outer - xyz_le_inner
            ) * (1 + 2 * section_taper_ratio) / (3 + 3 * section_taper_ratio)

            section_AC = section_MAC_le + np.array([
                chord_fraction * section_MAC_length,
                0.0,
                0.0,
            ])

            sectional_ACs.append(section_AC[0])

        sectional_AC_area_products = [
            AC * area
            for AC, area in zip(sectional_ACs, sectional_areas)
        ]

        return sum(sectional_AC_area_products) / sum(sectional_areas)

    
    def form_factor(self, mach)->float:

        sweep_thickness_to_chord_max = np.arctan(np.tan(self.sweep_LE_rad) + self.chord_fraction_maximum_thickness*2*self.c_root/self.span*(1-self.taper))
        
        FF = ( 1 + 0.6 / self.pos_max_camber * self.thickness_to_chord + 100 * self.thickness_to_chord ** 4 ) * (1.34 * mach ** 0.18 * np.cos(sweep_thickness_to_chord_max) ** 0.28)

        return FF
    

    def estimate_weight(self, mach:float, altitude:float)->float:
        #TODO implement planform weight estimation
        #maybe split into inherited classes
        pass #Use 2d lift parameters from self and EASA lift distributions. Make relevant assumptions about the structure
        #Put the relevant material properties in constants

    
    def cache_weight(self, name:str, mach:float, altitude:float)->float:
        self.weight_cache[name] = self.estimate_weight(mach, altitude)

