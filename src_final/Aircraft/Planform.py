import sys
import os
import matplotlib.pyplot as plt
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Drag.Component import Component
from global_parameters import Assumptions, CONSTANTS

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
        self.mass_cache:float = None

        #self.oswald = 4.61*(1 - 0.045 * self.aspect_ratio**.68)*np.cos(self.sweep_LE_rad)**0.15 - 3.1

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
    def positive_C_L_max(self)->float:
        return 0.9*self.clmax*np.cos(self.sweep_quarter_rad)

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
    
    @property 
    def inviscid_ratio(self)->float:
        return np.pi*self.aspect_ratio*self.oswald 
    
    @property
    def sweep_half_rad(self)->float:
        return np.arctan(np.tan(self.sweep_LE_rad) - 0.5 * (2*self.c_root/self.span) * (1-self.taper))
        
    @property
    def oswald(self)->float:
        return 2/(2 - self.aspect_ratio + np.sqrt(4 + self.aspect_ratio**2 * (1 + np.tan(self.sweep_half_rad)**2)))
    
    
    def sectional_properties(self,
                        number_of_sections)->tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray]:
        
        y_stations = np.linspace(0, self.half_span, number_of_sections)
    
        chord_stations = self.c_root + (self.c_tip - self.c_root) * y_stations / self.half_span
        
        dy = np.diff(y_stations)
        c_inner = chord_stations[:-1]
        c_outer = chord_stations[1:]
        
        return chord_stations, 0.5 * (c_inner + c_outer) * dy, y_stations,dy
    
    def aerodynamic_center(self,
                       number_of_sections: int,
                       chord_fraction: float = 0.25) -> float:

        y_stations = np.linspace(0, self.half_span, number_of_sections)
        c_stations = self.c_root + (self.c_tip - self.c_root) * y_stations / self.half_span
        x_le_stations = y_stations * np.tan(self.sweep_LE_rad)

        sectional_areas = self.sectional_properties(number_of_sections)[1]  # length: number_of_sections - 1
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
    

    def estimate_conservative_lift_distribution(self,
                                                diameter_fuselage: float,
                                                positive_manoeuvring_limit_load_factor: float,
                                                initial_total_aircraft_mass: float,
                                                number_of_stations: int,
                                                )->tuple[np.ndarray,np.ndarray]:
        
        stall_speed_at_max_positive_manoeuvre_load=np.sqrt(positive_manoeuvring_limit_load_factor*initial_total_aircraft_mass*CONSTANTS.G0/(0.5*CONSTANTS.AIR_DENSITY_SEA_LEVEL*self.wing_area*self.positive_C_L_max))

        sectional_chords, _, sectional_spanwise_positions,_ = self.sectional_properties(number_of_stations)
        sectional_chords, _, sectional_spanwise_positions,_=sectional_chords[1:], _,sectional_spanwise_positions[1:],_
        
        full_dy = np.diff(np.linspace(0, self.half_span, number_of_stations))
        index_closest_to_fuselage=np.argmin(np.abs(sectional_spanwise_positions - diameter_fuselage/2))

        easa_chord = 0.5*(sectional_chords+4/np.pi*self.MAC*np.sqrt(1-((sectional_spanwise_positions-diameter_fuselage/2)/(sectional_spanwise_positions[-1]-diameter_fuselage/2))**2))
        #print('Estimated chord (EASA): ',easa_chord)
        #print('Length of EASA chord: ',len(list(easa_chord)))

        full_sectional_lifts_schenk = 0.5*CONSTANTS.AIR_DENSITY_SEA_LEVEL*stall_speed_at_max_positive_manoeuvre_load**2*self.positive_C_L_max*easa_chord*full_dy
        reduced_sectional_lifts_schrenk = full_sectional_lifts_schenk[index_closest_to_fuselage:]
        reduced_sectional_spanwise_positions=sectional_spanwise_positions[index_closest_to_fuselage:]

        #print('Schrenk sectional lifts: ',reduced_sectional_lifts_schrenk)
        #print('Schrenk total lift: ',2*np.sum(reduced_sectional_lifts_schrenk))
        #print('Load factor: ',2*np.sum(reduced_sectional_lifts_schrenk)/(9.81*initial_total_aircraft_mass))
        
        modified_sectional_lifts_schrenk=(np.sum(full_sectional_lifts_schenk)/np.sum(reduced_sectional_lifts_schrenk))*reduced_sectional_lifts_schrenk
        #print('Total aircraft lift (modified Schenk): ',2*np.sum(modified_sectional_lifts_schrenk))
        #print('Load factor (modified): ',2*np.sum(reduced_sectional_lifts_schrenk)/(9.81*initial_total_aircraft_mass))

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        ax1.plot(reduced_sectional_spanwise_positions, reduced_sectional_lifts_schrenk)
        ax1.set_title('Schrenk')
        ax1.grid(True)

        ax2.plot(reduced_sectional_spanwise_positions, modified_sectional_lifts_schrenk)
        ax2.set_title('Modified Schrenk (conservative)')
        ax2.grid(True)

        plt.tight_layout()
        #plt.show()
        plt.close()

        return reduced_sectional_spanwise_positions, modified_sectional_lifts_schrenk

    
    # def cache_weight(self, name:str, mach:float, altitude:float)->float:
    #     self.weight_cache[name] = self.estimate_weight(mach, altitude)

if __name__=='__main__':
    
    interference_factor=1.0
    surface_wetted=1.0
    characteristic_length=1.0
    laminar_fraction=1.0
    component=Component(interference_factor,
                        surface_wetted,
                        characteristic_length,
                        laminar_fraction)
    planform=Planform(    aspect_ratio=20.0,
    span=2.0,
    sweep_quarter_deg=0.0,
    taper=1.0,
    thickness_to_chord=0.12,
    cm_quarter_chord=1.0,
    wetted_surface_ratio=1.0,
    interference_factor=1.0,
    clmax=1.5,
    flap=False,)

    planform.estimate_conservative_lift_distribution(diameter_fuselage=0.31,
                                                     positive_manoeuvring_limit_load_factor=6.0,
                                                     initial_total_aircraft_mass=50.0,
                                                     number_of_stations=100)

    






