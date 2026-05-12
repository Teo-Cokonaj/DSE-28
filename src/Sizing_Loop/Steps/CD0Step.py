import aerosandbox as asb
import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import os
import sys

current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.append(project_root)

from global_parameters import CONSTANTS, Assumptions
import Drag.component_method as dcm
from flight_envelope.flight_envelope import FlightEnvelope
from objects.aircraft_parameters import AircraftParameters
from objects.lifting_surface_planform import LiftingSurfacePlanform

class CD0Step():
    def __init__(self):
        pass

    def _planform_geometry(self, planform: LiftingSurfacePlanform, is_main_wing: bool) -> dict[str, float]:
        """
        Build the geometry dict expected by the drag 'Planform' from a
        'LiftingSurfacePlanform' instance.
        """
        if not isinstance(planform, LiftingSurfacePlanform):
            raise TypeError("_planform_geometry expects a LiftingSurfacePlanform instance")

        chord_root = float(planform.c_root)
        wing_span = float(planform.span)
        taper_ratio = float(planform.taper)
        sweep_le = float(planform.sweep_LE_rad)

        return {
            "chord_root": chord_root,
            "wing_span": wing_span,
            "taper_ratio": taper_ratio,
            "sweep_LE": sweep_le,
            "chord_fraction_max_thickness": 0.3, # comes from airfoil (dummy var)
            "pos_max_camber": 0.25,              # comes from airfoil (dummy var)
            "thickness_to_chord_ratio": 0.1,     # comes from airfoil (dummy var)
        }


    def build_planform_components(self, airplane: asb.Airplane):
        """
        Turn a list of wing planforms into the drag-model objects used by 
        the component method.
        """
        components = []
        source_list = getattr(airplane, "planforms", None)
        if source_list is None:
            raise ValueError("No planforms available on airplane: attach 'planforms' to the airplane before calling build_planform_components.")

        surface_factors = [
            (1.00, 1.07),  # main wing (1.00 for high wing, 1.1-1.4 for low wing)
            (1.04, 1.05),  # horizontal stabilizer (conv. 1.04-1.05; T-tail 1.04; H-tail 1.06-1.13; V-tail 1.03)
            (1.00, 1.05),  # vertical stabilizer (set IF to 1.00 and then adjust the hor. stab. value)
            (1.05, 1.07),  # canard, only if present (use values similar to the wing, prob lower)
        ]

        if len(source_list) > len(surface_factors):
            raise ValueError(f"Expected at most {len(surface_factors)} planforms, got {len(source_list)}.")

        for index, wing_or_planform in enumerate(source_list):
            is_main_wing = index == 0 
            geometry = self._planform_geometry(wing_or_planform, is_main_wing=is_main_wing)
            interference_factor, wetted_surface_multiplier = surface_factors[index]

            components.append(
                dcm.Planform(
                    interference_factor,
                    geometry,
                    0.1,      # laminar fraction (General aviation – classic production metal; subsonic!)
                    0.405e-5, # reynolds factor (Production sheet metal)
                    wetted_surface_multiplier
                )
            )

        main_wing_geometry = components[0].geometry_params
        surface_reference = main_wing_geometry["chord_root"] * (1 + main_wing_geometry["taper_ratio"]) / 2 * main_wing_geometry["wing_span"]
        return components, surface_reference

    def _fuselage_geometry(self) -> dict[str, float]:
        """
        Build the geometry dict expected by the drag 'Fuselage' from
        'Assumptions'. 
        """
        return {
            "length1": float(self.assumptions.fuselage_length1),
            "length2": float(self.assumptions.fuselage_length2),
            "length3": float(self.assumptions.fuselage_length3),
            "diameter": float(self.assumptions.diameter_fuselage),
            "upsweep": float(self.assumptions.fuselage_upsweep),
            "area_base": float(self.assumptions.fuselage_base_area),
        }

    def build_fuselage_components(self) -> dcm.Fuselage:
        """
        Build the fuselage drag component from assumptions.
        """
        geometry = self._fuselage_geometry()
        interference_factor = 1.0  # fuselage reference IF
        laminar_fraction = 0.05  # assume very low laminar fraction for fuselage
        
        return dcm.Fuselage(
            interference_factor,
            geometry,
            laminar_fraction,
            0.405e-5  # reynolds factor (Production sheet metal)
        )
        
    def _landing_gear_geometry(self) -> dict[str, float]:
        """
        Build nose and main landing-gear geometry dicts from 'Assumptions'.
        Returns a tuple: (nose_geometry, main_geometry)
        """
        nose_geometry = {
            "diameter_wheel": float(self.assumptions.nose_gear_diameter_wheel),
            "width_wheel": float(self.assumptions.nose_gear_width_wheel),
            "height_strut": float(self.assumptions.nose_gear_height_strut),
            "width_strut": float(self.assumptions.nose_gear_width_strut),
            "height_total": float(self.assumptions.nose_gear_diameter_wheel / 2 + self.assumptions.nose_gear_height_strut),
            "width_total": float(self.assumptions.nose_gear_width_strut + self.assumptions.nose_gear_width_wheel),
        }

        main_geometry = {
            "diameter_wheel": float(self.assumptions.main_gear_diameter_wheel),
            "width_wheel": float(self.assumptions.main_gear_width_wheel),
            "height_strut": float(self.assumptions.main_gear_height_strut),
            "width_strut": float(self.assumptions.main_gear_width_strut),
            "height_total": float(self.assumptions.main_gear_diameter_wheel / 2 + self.assumptions.main_gear_height_strut),
            "width_total": float(self.assumptions.main_gear_width_strut + self.assumptions.main_gear_width_wheel),
        }

        return nose_geometry, main_geometry

    def build_landing_gear_components(self) -> list:
        """
        Build 'LandingGear' components using assumptions.
        """
        nose_geom, main_geom = self._landing_gear_geometry()
        nose_component = dcm.LandingGear(nose_geom, bool(self.assumptions.nose_gear_enclosed))
        main_component = dcm.LandingGear(main_geom, bool(self.assumptions.main_gear_enclosed))
        return [nose_component, main_component]

    def _bay_geometry(self) -> dict[str, float]:
        """
        Build bay (nacelle) geometry from fuselage assumptions.
        Uses the sum of fuselage length sections as the bay length.
        """
        length_total = float(self.assumptions.fuselage_length1 + self.assumptions.fuselage_length2 + self.assumptions.fuselage_length3)
        diameter = float(self.assumptions.diameter_fuselage)
        return {
            "length": length_total,
            "diameter": diameter,
        }

    def build_bay_components(self) -> dcm.Bay:
        """
        Build a 'Bay' (nacelle) component using fuselage-derived length
        and diameter.
        """
        gp = self._bay_geometry()
        interference_factor = 1.3
        laminar_fraction = 0.1  # placeholder
        return dcm.Bay(
            interference_factor,
            float(gp["length"]),
            float(gp["diameter"]),
            laminar_fraction,
            0.405e-5  # reynolds factor (Production sheet metal)
        )

    def generate_lift_distribution(self, load_factor:float, plane:asb.Airplane)->asb.LiftingLine:
        return asb.LiftingLine()

    
    def estimate_CD0(self, airplane: asb.Airplane, mach: float, altitude: float, n_engines: float) -> float:
        """
        Estimate total CD0 using all currently modeled components.

        The current implementation combines:
        - planform components
        - fuselage
        - landing gear
        - bay / nacelle
        """
        planform_components, surface_reference = self.build_planform_components(airplane)
        fuselage_component = self.build_fuselage_components()
        landing_gear_components = self.build_landing_gear_components()
        bay_component = self.build_bay_component()

        all_components = (
            planform_components
            + [fuselage_component]
            + landing_gear_components
            + [bay_component]
        )

        return dcm.estimate_CD0(all_components, altitude, mach, surface_reference)