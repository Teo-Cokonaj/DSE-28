import numpy as np
import scipy.linalg as la
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..')))
from src_final.global_parameters import CONSTANTS, Assumptions
from src_final.structural_analysis.structural_matrices import StructuralMatrices
from src_final.structural_analysis.aerodynamic_matrices import AerodynamicMatrices
from src_final.structural_analysis.Material import Material
from src_final.Aircraft.Planform import Planform


class FlutterSolver:
    def __init__(self,
                  structural_matrices: StructuralMatrices,
                  aerodynamic_matrices: AerodynamicMatrices
                  ):
        self.A = structural_matrices.A_matrix()
        self.D = structural_matrices.D_matrix()
        self.E = structural_matrices.E_matrix()
        self.B = aerodynamic_matrices.B_matrix()
        self.C = aerodynamic_matrices.C_matrix()

    def _assemble_Q_matrix(self) -> np.ndarray:
        Q11 = np.zeros((2, 2))
        Q12 = np.eye(2)
        Q21 = -la.inv(self.A)@(self.C+self.E)
        Q22 = -la.inv(self.A)@(self.B+self.D)

        return np.block([[Q11, Q12],
                        [Q21, Q22]])
    
    def solve(self) -> tuple[np.ndarray, np.ndarray]:
        Q = self._assemble_Q_matrix()
        eigenvalues = la.eigvals(Q)
        
        #complex conjugate pairs so we keep only one per pair
        eigenvalues = eigenvalues[eigenvalues.imag > 0] 

        # Sort by ascending frequency for consistent mode ordering
        eigenvalues = eigenvalues[np.argsort(eigenvalues.imag)]

        omega = np.abs(eigenvalues)           # natural frequency [rad/s]
        zeta  = -eigenvalues.real / omega     # damping ratio [-]

        return omega, zeta
    
    
def flutter_sweep(airspeeds: np.ndarray,
                  altitude_m: float,
                  planform: Planform,
                  material: Material,
                  skin_thickness: float,
                  number_of_sections: int,
                  elastic_axis_fractional_position: float = 0.5
                  ) -> dict:
  
  omegas = []   # shape (n_speeds, n_modes)
  zetas  = []

  for V in airspeeds:
      structural_matrices = StructuralMatrices(planform=planform,
                                               material=material,
                                               skin_thickness=skin_thickness,
                                               number_of_sections=number_of_sections)
      aerodynamic_matrices = AerodynamicMatrices(planform=planform,
                                                 material=material,
                                                 skin_thickness=skin_thickness,
                                                 number_of_sections=number_of_sections,
                                                 airspeed=V,
                                                 altitude_m=altitude_m,
                                                 elastic_axis_fractional_position=elastic_axis_fractional_position)
      solver = FlutterSolver(structural_matrices,
                             aerodynamic_matrices)
      
      omega, zeta = solver.solve()
      omegas.append(omega)
      zetas.append(zeta)

  return {"omega": np.array(omegas), "zeta": np.array(zetas)}


if __name__=='__main__':
    print(1)