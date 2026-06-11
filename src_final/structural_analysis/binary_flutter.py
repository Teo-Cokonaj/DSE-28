import numpy as np
import scipy.linalg as la
import matplotlib.pyplot as plt
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
                  elastic_axis_fractional_position: float = 0.25
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
                                                 )
      solver = FlutterSolver(structural_matrices,
                             aerodynamic_matrices)
      
      omega, zeta = solver.solve()
      omegas.append(omega)
      zetas.append(zeta)

  return {"omega": np.array(omegas), "zeta": np.array(zetas)}


def plot_flutter_diagram(airspeeds: np.ndarray,
                         results: dict,
                         save_path: str = "flutter_diagram.png") -> None:

    omegas = results["omega"]   # (n_speeds, n_modes)
    zetas  = results["zeta"]    # (n_speeds, n_modes)
    n_modes = omegas.shape[1]
    mode_labels = ["Bending mode", "Torsion mode"]
    colors = ["steelblue", "tomato"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7), sharex=True)

    # --- V-omega plot ---
    for i in range(n_modes):
        ax1.plot(airspeeds, omegas[:, i] / (2 * np.pi),
                 color=colors[i], label=mode_labels[i])

    ax1.set_ylabel("Frequency [Hz]")
    ax1.set_ylim(bottom=0)
    ax1.legend()
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.set_title("Flutter Diagram")

    # --- V-zeta plot ---
    for i in range(n_modes):
        ax2.plot(airspeeds, zetas[:, i],
                 color=colors[i], label=mode_labels[i])

        # Mark flutter speed: first zero crossing from negative to positive
        sign_changes = np.where(np.diff(np.sign(zetas[:, i])))[0]
        for idx in sign_changes:
            if zetas[idx, i] < 0 and zetas[idx + 1, i] > 0:
                # Linear interpolation for accuracy
                V_flutter = np.interp(0,
                                      [zetas[idx, i], zetas[idx + 1, i]],
                                      [airspeeds[idx], airspeeds[idx + 1]])
                ax2.axvline(V_flutter, color=colors[i],
                            linestyle="--", alpha=0.7,
                            label=f"V_flutter ({mode_labels[i]}): {V_flutter:.1f} m/s")

    ax2.axhline(0, color="black", linewidth=0.8, linestyle="-")
    ax2.set_ylabel("Damping ratio ζ [-]")
    ax2.set_xlabel("Airspeed [m/s]")
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=450, bbox_inches="tight")

    plt.show()


if __name__=='__main__':
    
    airspeeds = np.arange(0.0,200.0,0.5)
    altitude_m = 6000.0
    material = Material(density=1600,
                            elastic_modulus=50e9,
                            shear_modulus=5e9,
                            poisson_ratio=0.3,
                            yield_strength=600e6,
                            fracture_strength=600e6
                            )
    planform_wing=Planform(
            aspect_ratio=27.0,
            span=2.67,
            sweep_quarter_deg=15.0,
            taper=0.5,
            thickness_to_chord=0.12,
            cm_quarter_chord=1.0,
            wetted_surface_ratio=1.0,
            interference_factor=1.0,
            clmax=1.5,
            flap=False,
        )

    results = flutter_sweep(airspeeds,
                  altitude_m=altitude_m,
                  planform=planform_wing,
                  material=material,
                  skin_thickness=0.004,
                  number_of_sections=100,
                  elastic_axis_fractional_position = 0.25
                  )
    
    plot_flutter_diagram(airspeeds=airspeeds,
                         results=results,
                         save_path="flutter_diagram.png")