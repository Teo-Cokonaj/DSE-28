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
                  aerodynamic_matrices: AerodynamicMatrices,
                  structural_damping: bool = True
                  ):
        self.A = structural_matrices.A_matrix()
        if structural_damping:
            self.D = structural_matrices.D_matrix()
        else:
            self.D = np.zeros_like(structural_matrices.D_matrix())
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
        eigenvalues = eigenvalues[np.argsort(np.abs(eigenvalues.imag))] #sorted

        sigma = eigenvalues.real
        omega = np.abs(eigenvalues.imag)

        magnitude = np.sqrt(sigma**2 + omega**2)
        eps = 1e-12
        magnitude = np.where(magnitude < eps, eps, magnitude)

        zeta = -sigma / magnitude

        return omega, zeta
    
    
def flutter_sweep(airspeeds: np.ndarray,
                  altitude_m: float,
                  planform: Planform,
                  material: Material,
                  skin_thickness: float,
                  number_of_sections: int,
                  elastic_axis_fractional_position: float = 0.50,
                  structural_damping: bool = True
                  ) -> dict:
  
    omegas = []   # shape (n_speeds, n_modes)
    zetas  = []

    for V in airspeeds:
        structural_matrices = StructuralMatrices(planform=planform,
                                                material=material,
                                                skin_thickness=skin_thickness,
                                                number_of_sections=number_of_sections,
                                                elastic_axis_fractional_position=elastic_axis_fractional_position)
        aerodynamic_matrices = AerodynamicMatrices(planform=planform,
                                                    material=material,
                                                    skin_thickness=skin_thickness,
                                                    number_of_sections=number_of_sections,
                                                    airspeed=V,
                                                    altitude_m=altitude_m,
                                                    fractional_distance_e=elastic_axis_fractional_position-0.25
                                                    )
        solver = FlutterSolver(structural_matrices,
                               aerodynamic_matrices,
                               structural_damping)
        
        omega, zeta = solver.solve()
        omegas.append(np.asarray(omega))
        zetas.append(np.asarray(zeta))

    return {"omega": np.array(omegas), "zeta": np.array(zetas)}


def plot_flutter_diagram(airspeeds: np.ndarray,
                         results: dict,
                         save_path: str = "flutter_diagram.png") -> None:

    omegas = np.asarray(results["omega"])
    zetas  = np.asarray(results["zeta"])

    if omegas.ndim == 1:
        omegas = omegas[:, None]
    if zetas.ndim == 1:
        zetas = zetas[:, None]

    n_modes = omegas.shape[1]

    base_labels = ["Bending mode", "Torsion mode"]
    mode_labels = [
        base_labels[i] if i < len(base_labels) else f"Mode {i+1}"
        for i in range(n_modes)
    ]

    colors = plt.cm.tab10.colors  # safe for many modes

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)

    # ============================================================
    # FREQUENCY PLOT
    # ============================================================
    for i in range(n_modes):

        freq_hz = omegas[:, i] / (2 * np.pi)

        # clean invalid values
        freq_hz = np.nan_to_num(freq_hz, nan=0.0, posinf=0.0, neginf=0.0)

        ax1.plot(
            airspeeds,
            freq_hz,
            color=colors[i % len(colors)],
            label=mode_labels[i]
        )

    ax1.set_ylabel("Frequency [Hz]")
    ax1.set_ylim(bottom=0)
    ax1.set_title("Flutter Diagram (Frequency & Damping)")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend()

    # ============================================================
    # DAMPING PLOT
    # ============================================================
    for i in range(n_modes):

        zeta = zetas[:, i]
        zeta = np.nan_to_num(zeta, nan=0.0, posinf=0.0, neginf=0.0)

        ax2.plot(
            airspeeds,
            zeta,
            color=colors[i % len(colors)],
            label=mode_labels[i]
        )

    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_ylabel("Damping ratio ζ [-]")
    ax2.set_xlabel("Airspeed [m/s]")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend()

    plt.tight_layout()
    plt.savefig(save_path, dpi=450, bbox_inches="tight")

    plt.show()


if __name__=='__main__':
    airspeeds = np.arange(1.0,270.0,1.0)
    altitude_m = 0.3048*27000

    material = Material(density=1600,
                            elastic_modulus=69e9,
                            shear_modulus=5.58e9,
                            poisson_ratio=0.048,
                            yield_strength=600e6,
                            fracture_strength=600e6
                            )
    
    planform_wing=Planform(
            aspect_ratio=27.0,
            span=2.67,
            sweep_quarter_deg=15.0,
            taper=0.3,
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
                  skin_thickness=0.0045,
                  number_of_sections=10,
                  elastic_axis_fractional_position = 0.50,
                  structural_damping = True
                  )
    
    plot_flutter_diagram(airspeeds=airspeeds,
                         results=results,
                         save_path="flutter_diagram.png")