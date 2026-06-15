import numpy as np
import scipy.linalg as la
import matplotlib.pyplot as plt
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..')))
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

    def _assemble_Q_matrix(self) ->     np.ndarray:
        Q11 = np.zeros((2, 2))
        Q12 = np.eye(2)
        Q21 = -la.inv(self.A)@(self.C+self.E)
        Q22 = -la.inv(self.A)@(self.B+self.D)

        return np.block([[Q11, Q12],
                        [Q21, Q22]])
    
    def solve(self) -> tuple[np.ndarray, np.ndarray]:
        Q = self._assemble_Q_matrix()
        eigenvalues = la.eigvals(Q)

        n_modes = Q.shape[0] // 2
        eigenvalues = eigenvalues[np.argsort(eigenvalues.imag)[::-1]][:n_modes]
        eigenvalues = eigenvalues[np.argsort(np.abs(eigenvalues))]

        magnitude = np.abs(eigenvalues)

        omega = np.where(magnitude<1e-8, 0.0, magnitude)
        zeta  = np.where(magnitude<1e-8, np.nan, -eigenvalues.real / magnitude)

        return omega, zeta
    
    
def flutter_sweep(airspeeds,
                  altitude_m,
                  planform,
                  material,
                  skin_thickness,
                  number_of_sections,
                  elastic_axis_fractional_position=0.50,
                  structural_damping=True) -> dict:

    omegas = []
    zetas  = []
    prev_all_eigenvalues = None

    for V in airspeeds:
        structural_matrices = StructuralMatrices(
            planform=planform,
            material=material,
            skin_thickness=skin_thickness,
            number_of_sections=number_of_sections,
            elastic_axis_fractional_position=elastic_axis_fractional_position)
        
        aerodynamic_matrices = AerodynamicMatrices(
            planform=planform,
            material=material,
            skin_thickness=skin_thickness,
            number_of_sections=number_of_sections,
            airspeed=V, altitude_m=altitude_m,
            fractional_distance_e=elastic_axis_fractional_position - 0.25,
            compressibility_correction=True)

        solver = FlutterSolver(structural_matrices,
                               aerodynamic_matrices,
                               structural_damping)
        
        Q = solver._assemble_Q_matrix()
        n_modes = Q.shape[0]//2
        n_total = Q.shape[0]

        eigenvalues_all = la.eigvals(Q)

        if prev_all_eigenvalues is None:
            eigenvalues_all = eigenvalues_all[np.argsort(eigenvalues_all.imag)[::-1]]
            top = eigenvalues_all[:n_modes]
            top = top[np.argsort(np.abs(top))]
            eigenvalues_all[:n_modes] = top

        else:
            order = []
            remaining = list(range(n_total))
            for prev_ev in prev_all_eigenvalues:
                mag_prev = np.abs(prev_ev)
                is_prev_real = (
                    np.abs(prev_ev.imag) / (mag_prev + 1e-16) < 1e-3
                )
                if is_prev_real:
                    dists = [abs(eigenvalues_all[j].real - prev_ev.real)
                             for j in remaining]
                else:
                    dists = [abs(eigenvalues_all[j] - prev_ev)
                             for j in remaining]
                best = remaining[int(np.argmin(dists))]
                order.append(best)
                remaining.remove(best)
            eigenvalues_all = eigenvalues_all[order]

        prev_all_eigenvalues = eigenvalues_all.copy()

        eigenvalues     = eigenvalues_all[:n_modes]
        eigenvalues_neg = eigenvalues_all[n_modes:]

        magnitude = np.abs(eigenvalues)
        imag_frac = np.where(magnitude < 1e-8, 0.0, np.abs(eigenvalues.imag) / magnitude)
        is_real   = imag_frac < 1e-3
        is_diverged = is_real & (eigenvalues.real > 0)

        sigma1 = eigenvalues.real
        sigma2 = eigenvalues_neg.real
        prod   = sigma1 * sigma2
        omega_n_real = np.sqrt(np.maximum(prod, 0.0))
        zeta_real = np.where(omega_n_real > 1e-8,
                             -(sigma1 + sigma2) / (2.0 * omega_n_real),
                             np.nan)

        omega = np.where(is_real | (magnitude < 1e-8), 0.0, magnitude)

        zeta = np.where(
            (magnitude < 1e-8) | is_diverged, np.nan,
            np.where(is_real, zeta_real, -eigenvalues.real / magnitude)
        )

        omegas.append(omega)
        zetas.append(zeta)

    return {"omega": np.array(omegas), "zeta": np.array(zetas)}


def plot_flutter_diagram(airspeeds,
                         results,
                         save_path="flutter_diagram.png"):

    omegas = np.asarray(results["omega"], dtype=float)
    zetas  = np.asarray(results["zeta"],  dtype=float)

    if omegas.ndim == 1: omegas = omegas[:, None]
    if zetas.ndim == 1:  zetas  = zetas[:, None]

    n_modes = omegas.shape[1]
    base_labels = ["Bending mode", "Torsion mode"]
    mode_labels = [base_labels[i] if i < len(base_labels) else f"Mode {i+1}"
                   for i in range(n_modes)]
    colors  = plt.cm.tab10.colors
    diverged = np.isnan(zetas)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 8), sharex=True)

    for i in range(n_modes):
        freq_hz = omegas[:, i] / (2 * np.pi)
        mask    = diverged[:, i]
        ax1.plot(airspeeds, np.where(mask, np.nan, freq_hz),
                 color=colors[i % len(colors)], label=mode_labels[i])

    ax1.set_ylabel("Frequency [Hz]")
    ax1.set_ylim(bottom=0)
    ax1.minorticks_on()
    ax1.grid(True, which="major", linestyle="--", alpha=0.5)
    ax1.grid(True, which="minor", linestyle=":",  alpha=0.3)
    ax1.legend()

    for i in range(n_modes):
        mask = diverged[:, i]
        ax2.plot(airspeeds, np.where(mask, np.nan, zetas[:, i]),
                 color=colors[i % len(colors)], label=mode_labels[i])

    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_ylabel("Damping ratio [-]")
    ax2.set_xlabel("Airspeed [m/s]")
    ax2.minorticks_on()
    ax2.grid(True, which="major", linestyle="--", alpha=0.5)
    ax2.grid(True, which="minor", linestyle=":",  alpha=0.3)
    ax2.legend()

    plt.tight_layout()
    plt.savefig(save_path, dpi=450, bbox_inches="tight")
    plt.show()


def extract_flutter_speed(airspeeds, results):
    zetas = np.asarray(results["zeta"], dtype=float)

    if zetas.ndim == 1:
        zetas = zetas[:, None]

    flutter_speeds = []

    for mode in range(zetas.shape[1]):
        zeta = zetas[:, mode]

        vf = None

        for i in range(len(airspeeds) - 1):

            z1, z2 = zeta[i], zeta[i + 1]

            if np.isnan(z1) or np.isnan(z2):
                continue

            if z1 > 0 and z2 <= 0:

                V1 = airspeeds[i]
                V2 = airspeeds[i + 1]
                vf = V1 - z1 * (V2 - V1) / (z2 - z1)

                break

        flutter_speeds.append(vf)

    return flutter_speeds


if __name__=='__main__':
    airspeeds = np.arange(1.0,271.0,1.0)
    altitude_m = 0.3048*27000 #altitude at max Mach

    material = Material(density=1600,
                            elastic_modulus=69e9,
                            shear_modulus=5.58e9,
                            poisson_ratio=0.048,
                            yield_strength=600e6,
                            fracture_strength=600e6
                            )
    
    planform_wing=Planform(
            aspect_ratio=27.0,
            span=3.2,
            sweep_quarter_deg=15.0,
            taper=0.3,
            thickness_to_chord=0.12,
            cm_quarter_chord=1.0,
            wetted_surface_ratio=1.0,
            interference_factor=1.0,
            clmax=1.5,
            flap=False,
        )
    
    thicknesses = np.arange(0.0045,0.0046,0.0001)
    flutter_speeds=[]
    divergence_speeds = []
    
    for thickness in thicknesses:
        results = flutter_sweep(airspeeds,
                    altitude_m=altitude_m,
                    planform=planform_wing,
                    material=material,
                    skin_thickness=thickness,
                    number_of_sections=100,
                    elastic_axis_fractional_position = 0.50,
                    structural_damping = True
        )

        flutter_speed = extract_flutter_speed(airspeeds, results)[1]
        flutter_speeds.append(flutter_speed)

    plot_flutter_diagram(airspeeds=airspeeds,
                         results=results,
                         save_path="flutter_diagram.png")