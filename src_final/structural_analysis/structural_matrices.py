import numpy as np
import scipy.integrate as integrate
import scipy.linalg as la
import pandas as pd
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..')))
from src_final.structural_analysis.Material import Material
from src_final.Aircraft.Planform import Planform
from src_final.global_parameters import CONSTANTS, Assumptions

assumptions = Assumptions ()
constants = CONSTANTS ()

class StructuralMatrices:
    def __init__(self,
                 planform: Planform,
                 material: Material,
                 skin_thickness: float,
                 number_of_sections: int,
                 elastic_axis_fractional_position: float = 0.5,
                 csv_path: str = 'src_final/structural_analysis/onshape_mass_distribution.csv'
                 ):
        self.root_chord = planform.c_root
        self.wing_span = planform.span
        self.semi_span = planform.half_span
        self.taper_ratio = planform.taper
        self.thickness_to_chord = planform.thickness_to_chord
        self.main_wing_area = planform.wing_area
        self.skin_thickness=skin_thickness
        self.E = material.elastic_modulus
        self.G = material.shear_modulus
        self.number_of_sections = number_of_sections
        self.chords, self.areas, self.y_stations,self. dy=planform.sectional_properties(self.number_of_sections)
        self.wing_thicknesses=self.thickness_to_chord*self.chords
        self.skin_thicknesses=np.ones_like(self.wing_thicknesses)*self.skin_thickness
        self.xf = elastic_axis_fractional_position * self.chords
        self.csv_path=csv_path

    def _mass_per_unit_area(self):
        
        df = pd.read_csv(self.csv_path)

        def get_mass(name_prefix: str):
            mask = df["Component Name"].str.startswith(name_prefix)
            if not mask.any():
                raise ValueError(f"CSV must contain a '{name_prefix}' entry.")
            return df[mask].iloc[0]["Mass (kg)"]
        
        self.main_wing_mass = get_mass("Main Wing")
        self.mass_per_unit_area = self.main_wing_mass / self.main_wing_area


    def _a11(self) -> float:
        self._mass_per_unit_area()
        multiplier = self.mass_per_unit_area #mass per unit area of the wing
        integrand = ((self.y_stations/self.semi_span)**4 * (self.chords))
        return multiplier*integrate.trapezoid(integrand,
                                              self.y_stations)

    def _a12(self) -> float:
        self._mass_per_unit_area()
        multiplier = self.mass_per_unit_area #mass per unit area of the wing
        integrand = ((self.y_stations/self.semi_span)**3 * ((self.chords**2)/2)) - ((self.y_stations/self.semi_span)**3 * (self.xf) * (self.chords))
        return multiplier*integrate.trapezoid(integrand,
                                              self.y_stations)
    
    def _a21(self) -> float:
        self._mass_per_unit_area()
        multiplier = self.mass_per_unit_area #mass per unit area of the wing
        integrand = ((self.y_stations/self.semi_span)**3 * ((self.chords**2)/2)) - ((self.y_stations/self.semi_span)**3 * (self.xf) * (self.chords))
        return multiplier*integrate.trapezoid(integrand,
                                              self.y_stations)
    
    def _a22(self) -> float:
        self._mass_per_unit_area()
        multiplier = self.mass_per_unit_area #mass per unit area of the wing
        integrand = ((self.y_stations/self.semi_span)**2 * ((self.chords**3)/3)) - ((self.y_stations/self.semi_span)**2 * ((self.chords**2) * (self.xf))) + ((self.y_stations/self.semi_span)**2 * (self.xf)**2 * (self.chords))
        return multiplier*integrate.trapezoid(integrand,
                                              self.y_stations)


    def A_matrix(self) -> np.matrix:
        matrix = np.matrix([[self._a11(), self._a12()],
                            [self._a21(), self._a22()]])
        
        
        return matrix

    
    def I(self) -> np.ndarray:
        a = self.chords/2
        b = self.thickness_to_chord * self.chords/2
        t = self.skin_thickness
        a_i = a-t
        b_i = b-t

        I = (np.pi / 4) * (a * b**3 - a_i * b_i**3)

        return I
    

    def J(self) -> np.ndarray:
        a = self.chords/2
        b = self.thickness_to_chord * self.chords/2
        t = self.skin_thickness
        U = np.pi * (a+b-t)*(1 + 0.258 * ((a-b)**2)/((a+b-t)**2))
        
        J = (4 * (np.pi**2) * t * ((a - 0.5 * t)**2 * (b + 0.5 * t)**2))/U

        return J

    def _e11(self) -> float:
        integrand = (4*self.E*self.I())/(self.semi_span**4)
        return integrate.trapezoid(integrand,
                                              self.y_stations)

    def _e22(self) -> float:
        integrand = (self.G*self.J())/(self.semi_span**2)
        return integrate.trapezoid(integrand,
                                              self.y_stations)
    
    def eigenvalues(self,
                    matrix):
        eigenvalues = la.eigvals(matrix)
        print('eigenvalues: ',eigenvalues)
        
        #complex conjugate pairs so we keep only one per pair
        eigenvalues = eigenvalues[eigenvalues.imag > 0] 
        print('eigenvalues: ',eigenvalues)

        # Sort by ascending frequency for consistent mode ordering
        eigenvalues = eigenvalues[np.argsort(eigenvalues.imag)]
        print('eigenvalues: ',eigenvalues)

        omega = np.abs(eigenvalues)           # natural frequency [rad/s]
        print('omega: ',omega)
        zeta  = -eigenvalues.real / omega     # damping ratio [-]
        print('zeta: ',zeta)

        return omega, zeta
    
    def E_matrix(self) -> np.matrix:
        matrix = np.matrix([[self._e11(), 0],
                            [0, self._e22()]])
        
        return matrix
    
    def D_matrix(self) -> np.matrix:
        print('Matrix A: ',self.A_matrix())
        omega_A, zeta_A =self.eigenvalues(self.A_matrix())
        print('omega_A: ',omega_A)
        omega_E, zeta_E=self.eigenvalues(self.E_matrix())
        alpha = 2*omega_A*omega_E*(zeta_E*omega_A-zeta_A*omega_E)/(omega_A**2-omega_E**2)
        beta = 2*(omega_A*zeta_A-omega_E*zeta_E)/(omega_A**2-omega_E**2)

        return alpha*self.A_matrix()+beta*self.E_matrix