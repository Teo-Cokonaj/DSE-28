import aerosandbox as asb
import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import os
import sys
from typing import Dict
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from global_parameters import CONSTANTS, Assumptions
from objects.aircraft_parameters import AircraftParameters
from objects.lifting_surface_planform import LiftingSurfacePlanform
from airfoil.SymmetricAirfoil import SymmetricAirfoil

#from aerodynamic_model.lifting_line_inviscid import asb.Lifting

class LiftingLineTheory():
    def __init__(self,
                 aircraft_parameters: AircraftParameters,
                 wing_planform: LiftingSurfacePlanform,
                 horizontal_stabilizer_planform: LiftingSurfacePlanform,
                 vertical_stabilizer_planform: LiftingSurfacePlanform,
                 canard_planform: LiftingSurfacePlanform = None,
                 wing_number_of_sections:int = 5,
                 horizontal_stabilizer_number_of_sections:int = 5,
                 canard_number_of_sections:int = 5,
                 vertical_stabilizer_number_of_sections:int = 5
                 ):
        
        self.aircraft_parameters=aircraft_parameters
        self.wing_planform = wing_planform
        self.horizontal_stabilizer_planform=horizontal_stabilizer_planform
        self.vertical_stabilizer_planform=vertical_stabilizer_planform
        self.canard_planform=canard_planform

        self.wing_number_of_sections = wing_number_of_sections
        self.horizontal_stabilizer_number_of_sections = horizontal_stabilizer_number_of_sections
        self.canard_number_of_sections = canard_number_of_sections
        self.vertical_stabilizer_number_of_sections = vertical_stabilizer_number_of_sections


    def initialize_airfoils(self,
                            airfoil_type: str):
        
        if airfoil_type =='custom':
            symmetric_airfoil = SymmetricAirfoil()
        else:
            symmetric_airfoil=asb.Airfoil(airfoil_type)         
        
        self.wing_airfoil = symmetric_airfoil
        self.horizontal_stabilizer_airfoil = symmetric_airfoil
        self.vertical_stabilizer_airfoil=symmetric_airfoil
        self.canard_airfoil = symmetric_airfoil
        self.wing_airfoils=np.array([self.wing_airfoil]*self.wing_number_of_sections)
        self.horizontal_stabilizer_airfoils=np.array([self.horizontal_stabilizer_airfoil]*\
                                                     self.horizontal_stabilizer_number_of_sections)
        self.vertical_stabilizer_airfoils=np.array([self.vertical_stabilizer_airfoil]*\
                                                   self.vertical_stabilizer_number_of_sections)
        self.canard_airfoils=np.array([self.canard_airfoil]*self.canard_number_of_sections)


    def calculate_LE_x_positions(self,
                                 number_of_sections: int,
                                 planform: LiftingSurfacePlanform):
        return np.linspace(0.0,planform.half_span*np.tan(planform.sweep_LE_rad),number_of_sections)


    def calculate_section_y_positions(self,
                                      number_of_sections: int,
                                      planform: LiftingSurfacePlanform):
        return np.linspace(0.0,planform.half_span,number_of_sections)


    def make_horizontal_lifting_surface(self,
        planform: LiftingSurfacePlanform,
        number_of_sections: int,
        twists: np.ndarray,
        airfoils: np.ndarray
    ) -> asb.Wing:

        xsecs = []

        section_LE_x_positions=self.calculate_LE_x_positions(number_of_sections,planform)
        section_y_positions=self.calculate_section_y_positions(number_of_sections,planform)

        chords = np.linspace(planform.c_root,planform.c_tip,number_of_sections)
        for i in range(number_of_sections):
            xsecs.append(
                asb.WingXSec(
                    xyz_le=np.array([section_LE_x_positions[i], section_y_positions[i], 0.0]),
                    chord=chords[i],
                    twist=twists[i],
                    airfoil=airfoils[i],
                )
            )

        return asb.Wing(
            symmetric=True,
            xsecs=xsecs,
        )
    

    def make_vertical_lifting_surface(self,
        planform: LiftingSurfacePlanform,
        number_of_sections: int,
        twists: np.ndarray,
        airfoils: np.ndarray,
    ) -> asb.Wing:

        xsecs = []

        section_LE_x_positions=self.calculate_LE_x_positions(number_of_sections,planform)
        section_y_positions = self.calculate_section_y_positions(number_of_sections,planform)

        chords=np.linspace(planform.c_root,planform.c_tip,number_of_sections)
        for i in range(number_of_sections):
            xsecs.append(
                asb.WingXSec(
                    xyz_le=np.array([section_LE_x_positions[i], 0.0, section_y_positions[i]]),
                    chord=chords[i],
                    twist=twists[i],
                    airfoil=airfoils[i],
                )
            )

        return asb.Wing(
            symmetric=False,
            xsecs=xsecs,
        )
    
    
    def make_full_airplane_model(self,
                                 main_wing: bool = True,
                                 canard: bool = False,
                                 horizontal_stabilizer: bool = False,
                                 vertical_stabilizer: bool = False):
        wings=[]
        if main_wing:
            wings.append(self.make_horizontal_lifting_surface(self.wing_planform,
                                                           self.wing_number_of_sections,
                                                           twists=np.linspace(0.0,
                                                                              self.wing_planform.tip_twist,
                                                                              self.wing_number_of_sections),
                                              airfoils=self.wing_airfoils))

        if canard:
            wings.append(self.make_horizontal_lifting_surface(self.canard_planform,
                                            self.canard_number_of_sections,
                                            twists=np.linspace(0.0,
                                                                self.canard_planform.tip_twist,
                                                                self.canard_number_of_sections),
                                            airfoils=self.canard_airfoils).translate(
                                                [-self.aircraft_parameters.canard_distance_in_front_of_wing,0.0,
                                                 self.aircraft_parameters.z_canard]
                                                ))

        if horizontal_stabilizer:
            wings.append(self.make_horizontal_lifting_surface(self.horizontal_stabilizer_planform,
                                                          self.horizontal_stabilizer_number_of_sections,
                                                          twists=np.linspace(0.0,
                                                                             self.horizontal_stabilizer_planform.tip_twist,
                                                                             self.horizontal_stabilizer_number_of_sections),
                                                          airfoils=self.horizontal_stabilizer_airfoils
                                            ).translate([self.aircraft_parameters.horizontal_stabilizer_distance_from_wing,0.0,
                                                         self.aircraft_parameters.z_horizontal_stabilizer])
        )

        if vertical_stabilizer:
            wings.append(self.make_vertical_lifting_surface(self.vertical_stabilizer_planform,
                                                          self.vertical_stabilizer_number_of_sections,
                                                          twists=np.linspace(0.0,0.0,self.vertical_stabilizer_number_of_sections),
                                                          airfoils=self.vertical_stabilizer_airfoils
                                            ).translate([self.aircraft_parameters.vertical_stabilizer_distance_from_wing,0.0,
                                                         self.aircraft_parameters.z_vertical_stabiliser_root])  
        )

        self.airplane = asb.Airplane(
            name="HUGO",
            xyz_ref=[0.0, 0.0, 0.0], #reference point
            wings=wings,
        )
    

    def find_aoa_for_force_equilibrium(self,
                         velocity: float,
                         altitude_m: float,
                         alpha_range=np.array([0., 5.]) #NOTE: must start with zero
                         ) -> float:
        if not np.isclose(alpha_range[0], 0.):
            raise ValueError("The range of angle of attacks must start with zero!")

        CL_sweep_results = self.run_llt_alpha_sweep(
            velocity=velocity,
            altitude_m=altitude_m,
            alpha_range_deg=alpha_range
        )
        CL_alpha = CL_sweep_results["lift_curve_slope_per_rad"]
        CL_alpha_equals_0 = CL_sweep_results["CL"][0]

        dynamic_pressure = .5 * velocity**2 * asb.Atmosphere(altitude_m).density()
        CL_target = self.aircraft_parameters.total_mass * CONSTANTS.G0 / dynamic_pressure / self.wing_planform.wing_area
        
        return np.rad2deg((CL_target - CL_alpha_equals_0) / CL_alpha)
        

    def run_llt_arbitrary_analysis(self,
                            altitude_m: float,
                            velocity: float,
                            angle_of_attack_deg: float,
                        ):

            self.op_point = asb.OperatingPoint(
                atmosphere=asb.Atmosphere(altitude_m),
                velocity=velocity,
                alpha=angle_of_attack_deg,
                beta=0,
                p=0,
                q=0,
                r=0,
            )

            def linear_spacing(start,end,number_of_stations):
                return np.linspace(0,1,number_of_stations)

            self.analysis = asb.LiftingLine(
                airplane=self.airplane,
                op_point=self.op_point,
                spanwise_spacing_function=linear_spacing,
            )

            results = self.analysis.run()

            return self.analysis, results
    
    
    def plot_lift_distribution(self):

        y = self.analysis.vortex_centers[:, 1]

        n = len(y)
        mid = len(y) // 2
        mask = np.ones(n, dtype=bool)
        mask[mid:] = False

        y=y[mask]        
        gamma = self.analysis.vortex_strengths
        gamma=(gamma[:,0])[mask]
        chord = self.analysis.chords[mask]
        area = self.analysis.areas[mask]

        V = self.analysis.op_point.velocity
        rho = self.analysis.op_point.atmosphere.density()

        lift_per_span = (rho * V * gamma) # Kutta-Joukowski lift per unit span
        dy = area / chord # Approximate panel span width
        panel_lift = lift_per_span * dy # Lift carried by each panel
        
        distributions = {
            "spanwise_stations": y,  #m
            "panel_lift": panel_lift,  #N
        }

        plt.plot(y,panel_lift)
        plt.show()

        return distributions
    
    
    def extract_L2_Di_ratio(self,
                            results: Dict) -> float:
        
        lift_coefficient=results['CL']#[0]
        drag_coefficient=results['CD']

        return lift_coefficient**2/drag_coefficient
    
    
    def run_llt_alpha_sweep(self,
                        velocity: float,
                        altitude_m: float,
                        alpha_range_deg: np.ndarray = np.arange(0, 5, 2),
                        ):
        Cm_list = []
        CL_list = []
        alpha_rad_list = []

        for alpha in alpha_range_deg:
            self.op_point = asb.OperatingPoint(
                atmosphere=asb.Atmosphere(altitude_m),
                velocity=velocity,
                alpha=float(alpha),
            )

            self.analysis = asb.LiftingLine(
                airplane=self.airplane,
                op_point=self.op_point,
            )

            results = self.analysis.run()

            CL_list.append(results["CL"])
            Cm_list.append(results["Cm"])
            alpha_rad_list.append(np.radians(float(alpha)))

        CL = np.array(CL_list)
        Cm = np.array(Cm_list)

        LEMAC_position_wrt_origin=self.wing_planform.x_MAC #origin at airplane reference point!!!

        AC_position_wrt_origin=self.airplane.wings[0].aerodynamic_center()[0] #origin at airplane reference point!!!

        x_ac=AC_position_wrt_origin-LEMAC_position_wrt_origin #origin at airplane reference point!!!
        C_L_alpha=(CL_list[-1]-CL_list[-2])/(alpha_rad_list[-2]-alpha_rad_list[-1])

        Cmac = np.polyfit(CL, Cm, 1)[1]  # intercept at CL=0

        CL = np.array(CL_list)
        Cm = np.array(Cm_list)
        
        return {
            "alpha": alpha_range_deg,
            "x_ac": x_ac,
            "CL": CL,
            "lift_curve_slope_per_rad":C_L_alpha,
            "Cmac":Cmac
        }            
        
    
if __name__ == "__main__":
    aircraft_parameters=AircraftParameters(total_mass=50.0,
                            horizontal_stabilizer_distance_from_wing=3.0,
                            vertical_stabilizer_distance_from_wing=3.0,
                            canard_distance_in_front_of_wing=0.5)

    horizontal=LiftingSurfacePlanform(aspect_ratio=3.0,
                                                                    span=0.5,
                                                                    sweep_quarter_deg=45.0,
                                                                    taper=1.0,
                                                                    tip_twist_rad=0.0)

    vertical=LiftingSurfacePlanform(aspect_ratio=3.0,
                                                                    span=0.3,
                                                                    sweep_quarter_deg=0.0,
                                                                    taper=0.3,
                                                                    tip_twist_rad=0.0)

    canard=LiftingSurfacePlanform(aspect_ratio=3.0,
                                                                    span=0.3,
                                                                    sweep_quarter_deg=45.0,
                                                                    taper=1.0,
                                                                    tip_twist_rad=0.0)

    altitude_m = 0.0
    atmosphere=asb.Atmosphere(altitude_m)
    velocity_incompressible=30.0
    velocity_compressible=200.0
    from global_parameters import Assumptions
    assumptions=Assumptions()

    import json
    import os

    RESULTS_FILE = "llt_results.jsonl"

    # ── Load existing results ────────────────────────────────────────────────────
    results_db = {}
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    entry = json.loads(line)
                    results_db[entry["key"]] = entry

    def _key(airfoil: str, sweep: float, taper: float, aoa_deg: float) -> str:
        """Canonical key for a single simulation point."""
        return f"{airfoil}__sweep{int(sweep):02d}__taper{taper:.2f}__aoa{float(aoa_deg):+.1f}"

    def _save_entry(key: str) -> None:
        """Append a single new result to the file. Never rewrites existing data."""
        entry = results_db[key]
        with open(RESULTS_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

    # ── Simulation loop ──────────────────────────────────────────────────────────
    angles_of_attack_deg = np.arange(0, 8, 1)
    airfoils             = ['NACA0008','NACA0010', 'NACA0012', 'custom']
    sweeps               = np.arange(0, 16, 5)
    tapers               = np.arange(0.1, 1.0, 0.1) 
    wing_number_of_sections=30
    angles_of_attack_rad = np.radians(angles_of_attack_deg)
    print('Reynolds incompressible: ',atmosphere.density()*velocity_incompressible*(2.0/27.0)/atmosphere.dynamic_viscosity())
    print('Reynolds compressible: ',atmosphere.density()*velocity_compressible*(2.0/27.0)/atmosphere.dynamic_viscosity())

    # AoA range used exclusively for the 2D RMS plots
    AOA_RMS_MIN, AOA_RMS_MAX = 0, 5   # degrees, inclusive

    for airfoil in airfoils:
        for sweep in sweeps:
            for taper in tapers:
                for angle_of_attack_deg in angles_of_attack_deg:

                    k = _key(airfoil, sweep, taper, angle_of_attack_deg)

                    # ── Incompressible ───────────────────────────────────────────
                    k_inc = k + "__inc"
                    if k_inc not in results_db:
                        main = LiftingSurfacePlanform(aspect_ratio=27.0,
                                                    span=2.0,
                                                    sweep_quarter_deg=float(sweep),
                                                    taper=float(taper),
                                                    tip_twist_rad=0.0)
                        lifting_line_theory = LiftingLineTheory(aircraft_parameters,
                                                                main, horizontal,
                                                                vertical, canard)
                        lifting_line_theory.wing_number_of_sections = wing_number_of_sections
                        lifting_line_theory.initialize_airfoils(airfoil)
                        lifting_line_theory.make_full_airplane_model(
                            main_wing=True, canard=False,
                            horizontal_stabilizer=False, vertical_stabilizer=False)

                        _, res_inc = lifting_line_theory.run_llt_arbitrary_analysis(
                            altitude_m, velocity_incompressible, float(angle_of_attack_deg))

                        reference_incompressible_slope = (
                            assumptions.airfoil_C_l_alpha
                            / (1 + assumptions.airfoil_C_l_alpha
                            / np.pi / lifting_line_theory.wing_planform.aspect_ratio)
                        )

                        results_db[k_inc] = {
                            "key":              k_inc,
                            "airfoil":          airfoil,
                            "sweep_deg":        float(sweep),
                            "taper":            float(taper),
                            "aoa_deg":          float(angle_of_attack_deg),
                            "flow":             "incompressible",
                            "CL":               float(res_inc["CL"]),
                            "CL_ref":           float(np.radians(angle_of_attack_deg)
                                                    * reference_incompressible_slope),
                            "reference_slope":  float(reference_incompressible_slope),
                        }
                        _save_entry(k_inc)
                        print(f"[new]   {k_inc}")
                    else:
                        print(f"[cache] {k_inc}")

                    # ── Compressible ─────────────────────────────────────────────
                    k_comp = k + "__comp"
                    if k_comp not in results_db:
                        main = LiftingSurfacePlanform(aspect_ratio=27.0,
                                                    span=2.0,
                                                    sweep_quarter_deg=float(sweep),
                                                    taper=float(taper),
                                                    tip_twist_rad=0.0)
                        lifting_line_theory = LiftingLineTheory(aircraft_parameters,
                                                                main, horizontal,
                                                                vertical, canard)
                        lifting_line_theory.wing_number_of_sections = wing_number_of_sections
                        lifting_line_theory.initialize_airfoils(airfoil)
                        lifting_line_theory.make_full_airplane_model(
                            main_wing=True, canard=False,
                            horizontal_stabilizer=False, vertical_stabilizer=False)

                        _, res_comp = lifting_line_theory.run_llt_arbitrary_analysis(
                            altitude_m, velocity_compressible, float(angle_of_attack_deg))

                        sweep_half_rad = np.arctan(
                            np.tan(lifting_line_theory.wing_planform.sweep_LE_rad)
                            - 0.5 * 2 * lifting_line_theory.wing_planform.c_root
                            / lifting_line_theory.wing_planform.span
                            * (1 - lifting_line_theory.wing_planform.taper)
                        )
                        mach  = velocity_compressible / atmosphere.speed_of_sound()
                        beta  = np.sqrt(1 - mach**2)
                        if airfoil == 'custom':
                            kappa = (1.0 / np.radians(9.0)) / (2 * np.pi)
                        elif airfoil == 'NACA0012':
                            kappa = (1.0 / np.radians(9.0)) / (2 * np.pi)
                        elif airfoil == 'NACA0010':
                            kappa = (1.0 / np.radians(9.5)) / (2 * np.pi)
                        elif airfoil == 'NACA0008':
                            kappa = (1.0/np.radians(9.5))/(2*np.pi)
                        else:
                            raise ValueError()
                        reference_compressible_slope = (
                            2 * np.pi * lifting_line_theory.wing_planform.aspect_ratio
                            / (2 + np.sqrt(
                                4 + (lifting_line_theory.wing_planform.aspect_ratio * beta / kappa)**2
                                * (1 + np.tan(sweep_half_rad)**2 / beta**2)
                            ))
                        )

                        results_db[k_comp] = {
                            "key":              k_comp,
                            "airfoil":          airfoil,
                            "sweep_deg":        float(sweep),
                            "taper":            float(taper),
                            "aoa_deg":          float(angle_of_attack_deg),
                            "flow":             "compressible",
                            "CL":               float(res_comp["CL"]),
                            "CL_ref":           float(np.radians(angle_of_attack_deg)
                                                    * reference_compressible_slope),
                            "reference_slope":  float(reference_compressible_slope),
                            "mach":             float(mach),
                            "beta":             float(beta),
                            "sweep_half_rad":   float(sweep_half_rad),
                        }
                        _save_entry(k_comp)
                        print(f"[new]   {k_comp}")
                    else:
                        print(f"[cache] {k_comp}")

    # ── CL-alpha plots (full AoA range, one figure per airfoil/sweep/taper) ─────
    for airfoil in airfoils:
        for sweep in sweeps:
            for taper in tapers:

                case_CL_incompressible     = []
                case_CL_ref_incompressible = []
                case_CL_compressible       = []
                case_CL_ref_compressible   = []

                for angle_of_attack_deg in angles_of_attack_deg:
                    k     = _key(airfoil, sweep, taper, angle_of_attack_deg)
                    e_inc  = results_db[k + "__inc"]
                    e_comp = results_db[k + "__comp"]
                    case_CL_incompressible.append(e_inc["CL"])
                    case_CL_ref_incompressible.append(e_inc["CL_ref"])
                    case_CL_compressible.append(e_comp["CL"])
                    case_CL_ref_compressible.append(e_comp["CL_ref"])

                case_CL_incompressible     = np.array(case_CL_incompressible)
                case_CL_ref_incompressible = np.array(case_CL_ref_incompressible)
                case_CL_compressible       = np.array(case_CL_compressible)
                case_CL_ref_compressible   = np.array(case_CL_ref_compressible)

                fig, ax = plt.subplots(figsize=(6, 4))
                ax.plot(angles_of_attack_deg, case_CL_incompressible,
                        'o-',  color='tab:blue', linewidth=0.5, markersize=3,
                        label='Incompressible — simulation')
                ax.plot(angles_of_attack_deg, case_CL_ref_incompressible,
                        'o--', color='tab:blue', linewidth=0.5, markersize=3,
                        label='Incompressible — Prandtl')
                ax.plot(angles_of_attack_deg, case_CL_compressible,
                        'o-',  color='tab:red', linewidth=0.5, markersize=3,
                        label='Compressible — simulation')
                ax.plot(angles_of_attack_deg, case_CL_ref_compressible,
                        'o--', color='tab:red', linewidth=0.5, markersize=3,
                        label='Compressible — DATCOM')
                ax.set_ylabel(r'$C_L$')
                ax.set_xlabel(r'$\alpha$ [deg]')
                ax.set_title(f'Airfoil: {airfoil} | Sweep: {sweep}° | Taper: {taper:.2f}')
                ax.grid(True, which='both', linestyle='--', linewidth=0.4, alpha=0.7)
                ax.minorticks_on()
                ax.legend(fontsize=7)
                fig.tight_layout()
                filename = f'CL_alpha_{airfoil}_sweep{int(sweep):02d}deg_taper{taper:.2f}.png'
                fig.savefig(filename, dpi=150)
                plt.close(fig)
                print(f'  Figure saved: {filename}')

    # ── 2D RMS plots (sweep × taper, filtered AoA range) ────────────────────────
    # axes: rows = sweeps, cols = tapers
    aoa_mask = (angles_of_attack_deg >= AOA_RMS_MIN) & (angles_of_attack_deg <= AOA_RMS_MAX)

    for airfoil in airfoils:
        for flow, suffix, ref_label in [
            ("incompressible", "__inc",  "incompressible"),
            ("compressible",   "__comp", "compressible"),
        ]:
            # rms_grid[i, j] = RMS error for sweeps[i], tapers[j]
            rms_grid = np.zeros((len(sweeps), len(tapers)))

            for i, sweep in enumerate(sweeps):
                for j, taper in enumerate(tapers):
                    errors = []
                    for angle_of_attack_deg in angles_of_attack_deg[aoa_mask]:
                        k = _key(airfoil, sweep, taper, angle_of_attack_deg) + suffix
                        e = results_db[k]
                        errors.append(e["CL"] - e["CL_ref"])
                    rms_grid[i, j] = np.sqrt(np.mean(np.array(errors)**2))

            fig, ax = plt.subplots(figsize=(6, 4))
            # pcolormesh expects edges; build them from cell centres
            sweep_edges = np.append(sweeps  - (sweeps[1]  - sweeps[0])  / 2,
                                    sweeps[-1]  + (sweeps[1]  - sweeps[0])  / 2)
            taper_edges = np.append(tapers  - (tapers[1]  - tapers[0])  / 2,
                                    tapers[-1]  + (tapers[1]  - tapers[0])  / 2)
            pcm = ax.pcolormesh(taper_edges, sweep_edges, rms_grid,
                                cmap='viridis', shading='flat')
            fig.colorbar(pcm, ax=ax, label=r'RMS $\Delta C_L$')
            ax.set_xlabel('Taper ratio')
            ax.set_ylabel('Sweep (quarter-chord) [deg]')
            ax.set_yticks(sweeps)
            ax.set_xticks(tapers)
            ax.set_title(f'RMS $C_L$ error | {airfoil} | {flow}\n'
                        f'AoA range: {AOA_RMS_MIN}° to {AOA_RMS_MAX}°')
            fig.tight_layout()
            filename = f'RMS_error_{airfoil}_{flow}.png'
            fig.savefig(filename, dpi=150)
            plt.close(fig)
            print(f'  Figure saved: {filename}')