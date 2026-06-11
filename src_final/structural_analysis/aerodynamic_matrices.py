import numpy as np
import scipy.integrate as integrate
import scipy.linalg as la
import os
import sys
from aerosandbox import Atmosphere
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..')))
from src_final.structural_analysis.Material import Material
from src_final.Aircraft.Planform import Planform
from src_final.global_parameters import CONSTANTS, Assumptions

assumptions = Assumptions ()
constants = CONSTANTS ()

class AerodynamicMatrices:
    def __init__(self,
                 planform: Planform,
                 material: Material,
                 skin_thickness: float,
                 number_of_sections: int,
                 airspeed: float,
                 altitude_m: float,
                 elastic_axis_fractional_position: float = 0.5
                 ):
        self.root_chord = planform.c_root
        self.wing_span = planform.span
        self.taper_ratio = planform.taper
        self.thickness_to_chord = planform.thickness_to_chord
        self.skin_thickness=skin_thickness
        self.E = material.elastic_modulus
        self.G=material.shear_modulus
        self.number_of_sections = number_of_sections
        self.chords, self.areas, self.y_stations,self. dy=planform.sectional_properties(self.number_of_sections)
        self.wing_thicknesses=self.thickness_to_chord*self.chords
        self.skin_thicknesses=np.ones_like(self.wing_thicknesses)*self.skin_thickness
        self.wing_lift_slope=planform.CL_alpha
        self.airspeed=airspeed
        self.atmosphere=Atmosphere(altitude_m)
        self.half_span = planform.half_span
        self.e = elastic_axis_fractional_position
        self.M_thetadot = -1.2 #do not change this
        print('y_stations: ',self.y_stations)


    def _b11(self) -> float:
        multiplier = 0.5*self.atmosphere.density()*self.airspeed*self.wing_lift_slope
        integrand = (self.y_stations/self.half_span)**4*self.chords

        return multiplier*integrate.trapezoid(integrand,
                                              self.y_stations)

    def _b12(self) -> float:

        return 0.0
    
    def _b21(self) -> float:
        multiplier = -0.5*self.atmosphere.density()*self.airspeed*self.e*self.wing_lift_slope
        integrand = (self.y_stations/self.half_span)**3*self.chords**2

        return multiplier*integrate.trapezoid(integrand,
                                              self.y_stations)
    
    def _b22(self) -> float:
        multiplier = -0.5* self.atmosphere.density()*self.airspeed*self.M_thetadot/4
        integrand = (self.y_stations/self.half_span)**2*self.chords**3

        return multiplier*integrate.trapezoid(integrand,
                                              self.y_stations)
    
    def _c11(self) -> float:

        return 0.0
    
    def _c21(self) -> float:

        return 0.0
    
    def _c12(self) -> float:
        multiplier = 0.5*self.atmosphere.density()*self.airspeed**2*self.wing_lift_slope
        integrand = (self.y_stations/self.half_span)**3*self.chords

        return multiplier*integrate.trapezoid(integrand,
                                              self.y_stations)
    
    def _c22(self) -> float:
        multiplier = -0.5*self.atmosphere.density()*self.airspeed**2*self.e*self.wing_lift_slope*
        integrand =  (self.y_stations/self.half_span)**2*self.chords**2

        return multiplier*integrate.trapezoid(integrand,
                                              self.y_stations)


    def B_matrix(self) -> np.matrix:
        matrix = np.matrix([[self._b11(), self._b12()],
                            [self._b21(), self._b22()]])
        
        return matrix
    
    def C_matrix(self) -> np.matrix:
        matrix = np.matrix([[self._c11(), self._c12()],
                            [self._c21(), self._c22()]])
        
        return matrix
