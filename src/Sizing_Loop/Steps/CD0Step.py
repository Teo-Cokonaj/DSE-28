import aerosandbox as asb
import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import os
import sys

current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.append(project_root)

from Sizing_Loop.DesignOptionState import DesignOptionState
from global_parameters import CONSTANTS, Assumptions
import Drag.component_method as dcm
from flight_envelope.flight_envelope import FlightEnvelope
from objects.aircraft_parameters import AircraftParameters
from objects.lifting_surface_planform import LiftingSurfacePlanform
from Sizing_Loop.DesignOptionStep import DesignOptionStep

class CD0Step(DesignOptionStep):
    def __init__(self, print_:bool=True):
        self.print_ = print_

    def update(self, state:DesignOptionState):
        assumptions = state.fixed.assumptions

        state.iterable.performance_parameters.cruise_parameters.CD0 = self.estimate_CD0(state, CONSTANTS.MACH_CRUISE, assumptions.ALTITUDE_CRUISE)

        state.iterable.performance_parameters.mach_max_parameters.CD0 = self.estimate_CD0(state, CONSTANTS.MACH_MAX, CONSTANTS.ALTITUDE_MACH_MAX)

        state.iterable.performance_parameters.go_around_parameters.CD0 = self.estimate_CD0(state, state.mach_go_around(), assumptions.ALTITUDE_GO_AROUND)

        #NOTE: using approach speed since takeoff and landing configurations are same for this aircraft
        takeoff_mach = assumptions.airspeed_approach / asb.Atmosphere().speed_of_sound() 
        state.iterable.performance_parameters.takeoff_parameters.CD0 = self.estimate_CD0(state, takeoff_mach, 0., True)

        state.iterable.performance_parameters.climb_OEI_parameters.CD0 = self.estimate_CD0(state, takeoff_mach, CONSTANTS.ALTITUDE_OEI_CLIMB, False)

        return state.iterable


    def _planform_geometry(self, planform: LiftingSurfacePlanform, diameter_fuselage:float, assumptions:Assumptions) -> dict[str, float]:
        """
        Build the geometry dict expected by the drag 'Planform' from a
        'LiftingSurfacePlanform' instance.
        """

        chord_root = float(planform.c_root)
        wing_span = float(planform.span)
        taper_ratio = float(planform.taper)
        sweep_le = float(planform.sweep_LE_rad)

        return {
            "diameter_fuselage": diameter_fuselage,
            "chord_root": chord_root,
            "wing_span": wing_span,
            "taper_ratio": taper_ratio,
            "sweep_LE": sweep_le,
            "chord_fraction_max_thickness": assumptions.airfoil_thickness_to_chord_max_location, # comes from airfoil (dummy var)
            "pos_max_camber": assumptions.max_camber_position,              # comes from airfoil (dummy var)
            "thickness_to_chord_ratio": assumptions.airfoil_thickness_to_chord_max,     # comes from airfoil (dummy var)
        }


    def build_planform_components(self, state:DesignOptionState) -> list[dcm.Planform]:
        """
        Turn a list of wing planforms into the drag-model objects used by 
        the component method.
        """
        planforms = state.iterable.lifting_surfaces
        diameter_fuselage = state.fixed.assumptions.diameter_fuselage
        components = list()

        surface_factors = [
            (state.fixed.choices.wing_interference_factor, 1.07),  # main wing (1.00 for high wing, 1.1-1.4 for low wing)
            (1.04, 1.05),  # horizontal stabilizer (conv. 1.04-1.05; T-tail 1.04; H-tail 1.06-1.13; V-tail 1.03)
            (1.00, 1.05),  # vertical stabilizer (set IF to 1.00 and then adjust the hor. stab. value)
            (1.05, 1.07),  # canard, only if present (use values similar to the wing, prob lower)
        ]

        if len(planforms) > len(surface_factors):
            raise ValueError(f"Expected at most {len(surface_factors)} planforms, got {len(planforms)}.")

        for index, wing_or_planform in enumerate(planforms):
            geometry = self._planform_geometry(wing_or_planform, diameter_fuselage, state.fixed.assumptions)
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

        return components

    def _fuselage_geometry(self, state:DesignOptionState) -> dict[str, float]:
        """
        Build the geometry dict expected by the drag 'Fuselage' from
        'Assumptions'. 
        """
        return {
            "length1": float(state.fixed.assumptions.fuselage_length1),
            "length2": float(state.fixed.assumptions.fuselage_length2),
            "length3": float(state.fixed.assumptions.fuselage_length3),
            "diameter": float(state.fixed.assumptions.diameter_fuselage),
            "upsweep": float(state.fixed.assumptions.fuselage_upsweep),
            "area_base": float(state.fixed.assumptions.fuselage_base_area),
        }

    def build_fuselage_components(self, state:DesignOptionState) -> dcm.Fuselage:
        """
        Build the fuselage drag component from assumptions.
        """
        geometry = self._fuselage_geometry(state)
        interference_factor = 1.0  # fuselage reference IF
        laminar_fraction = state.fixed.assumptions.fuselage_laminar_frac
        
        return dcm.Fuselage(
            interference_factor,
            geometry,
            laminar_fraction,
            0.405e-5  # reynolds factor (Production sheet metal)
        )
        
    def _landing_gear_geometry(self, state:DesignOptionState) -> dict[str, float]:
        """
        Build nose and main landing-gear geometry dicts from 'Assumptions'.
        Returns a tuple: (nose_geometry, main_geometry)
        """
        gear_effective_height = state.iterable.landing_gear.length_z
        gear_exposed_height = gear_effective_height - state.fixed.assumptions.diameter_fuselage / 2

        gear_effective_length = state.iterable.landing_gear.length_pythagorean() if state.fixed.choices.landing_gear_sideways_extendable else gear_effective_height
        gear_exposed_length = gear_effective_length - state.fixed.assumptions.diameter_fuselage / 2

        nose_geometry = {
            "diameter_wheel": float(state.fixed.assumptions.nose_gear_diameter_wheel),
            "width_wheel": float(state.fixed.assumptions.nose_gear_width_wheel),
            "height_strut": gear_exposed_height,
            "width_strut": float(state.fixed.assumptions.nose_gear_width_strut),
            "height_total": float(state.fixed.assumptions.nose_gear_diameter_wheel / 2 + gear_exposed_height),
            "width_total": float(state.fixed.assumptions.nose_gear_width_strut + state.fixed.assumptions.nose_gear_width_wheel),
        }

        main_geometry = {
            "diameter_wheel": float(state.fixed.assumptions.main_gear_diameter_wheel),
            "width_wheel": float(state.fixed.assumptions.main_gear_width_wheel),
            "height_strut": gear_exposed_length,
            "width_strut": float(state.fixed.assumptions.main_gear_width_strut),
            "height_total": float(state.fixed.assumptions.main_gear_diameter_wheel / 2 + gear_exposed_length),
            "width_total": float(state.fixed.assumptions.main_gear_width_strut + state.fixed.assumptions.main_gear_width_wheel),
        }

        if self.print_:
            print()
            print(f"Nose lg geometry: {nose_geometry}")
            print(f"Main geometry: {main_geometry}")
            print(f"exposed len: {gear_exposed_length}, effective len: {gear_effective_length}")

        return nose_geometry, main_geometry

    def build_landing_gear_components(self, state:DesignOptionState) -> list[dcm.LandingGear]:
        """
        Build 'LandingGear' components using assumptions.
        """
        nose_geom, main_geom = self._landing_gear_geometry(state)
        nose_component = dcm.LandingGear(nose_geom, bool(state.fixed.assumptions.nose_gear_enclosed))
        main_component = dcm.LandingGear(main_geom, bool(state.fixed.assumptions.main_gear_enclosed))

        if self.print_:
            for c in [nose_component, main_component, main_component]:
                print(f"surface frontal = {c.surface_frontal}, surface_reference = {c.surface_reference}")

        return [nose_component, main_component, main_component] #NOTE: there is a pair of main landing gears!


    def _bay_geometry(self, state:DesignOptionState) -> dict[str, float]:
        """
        Build bay (nacelle) geometry from fuselage assumptions.
        Uses the sum of fuselage length sections as the bay length.
        """
        return [
            {
                "length": state.iterable.propulsion_parameters.engine_parameters.length,
                "diameter": state.iterable.propulsion_parameters.engine_parameters.diameter,
            },
        ] * state.iterable.propulsion_parameters.n_engines

    
    def build_bay_components(self, state:DesignOptionState) -> list[dcm.Bay]:
        """
        Build a 'Bay' (nacelle) component using fuselage-derived length
        and diameter.
        """
        gps = self._bay_geometry(state)
        interference_factor = 1.3
        laminar_fraction = state.fixed.assumptions.wing_bay_laminar_frac  # placeholder
        bays = list()
        for gp in gps:
            bays.append(dcm.Bay(
                interference_factor,
                float(gp["length"]),
                float(gp["diameter"]),
                laminar_fraction,
                0.405e-5  # reynolds factor (Production sheet metal)
        ))
            
        if not state.fixed.choices.landing_gear_sideways_extendable:
            retracting_landing_gear_height = state.fixed.assumptions.main_gear_diameter_wheel / 2 + state.iterable.landing_gear.length_z

            bays.extend([
                dcm.Bay(
                    interference_factor=1.3,
                    laminar_fraction=laminar_fraction,
                    length=state.fixed.assumptions.lg_bay_length_safety_factor * retracting_landing_gear_height,
                    diameter=state.fixed.assumptions.lg_bay_wheel_diameter_ratio * state.fixed.assumptions.main_gear_diameter_wheel,
                    surface_reynolds_factor=0.405e-5  # reynolds factor (Production sheet metal)
                )
            ] * 2)

        return bays

    
    def estimate_CD0(self, state:DesignOptionState, mach: float, altitude: float, gear_down:bool=False) -> float:
        """
        Estimate total CD0 using all currently modeled components.

        The current implementation combines:
        - planform components
        - fuselage
        - landing gear
        - nacelles (bay components)
        """
        planform_components = self.build_planform_components(state)
        fuselage_component = self.build_fuselage_components(state)
        landing_gear_components = self.build_landing_gear_components(state) if gear_down else []
        bay_components = self.build_bay_components(state)

        all_components = (
            planform_components
            + [fuselage_component]
            + landing_gear_components
            + bay_components
        )

        surface_reference = state.iterable.lifting_surfaces[0].wing_area

        return dcm.estimate_CD0(all_components, altitude, mach, surface_reference)