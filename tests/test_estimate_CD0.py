import pytest as pt
import aerosandbox.numpy as np
import sys
import os

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import src.Drag.component_method as dcm

class TestCD0Estimate:
    def test_compare_with_year2_aircraft(self):
        #===IMPORTED GEOMETRY===
        wing_geometry = {
            'chord_root': 3.9848589773733183,
            'wing_span': 22.62783813,
            'taper_ratio': 0.352,
            'diameter_fuselage': 2.9,
            'sweep_LE': np.deg2rad(16.46),
            'chord_fraction_max_thickness': 0.3, 
            'pos_max_camber': 0.25,
            'thickness_to_chord_ratio': .1
        }

        fuselage_geometry = {
            'length1': 5.228340969042026,
            'length2': 19.44007435173294,
            'length3': 7.261584679225036,
            'diameter':2.9,
            'upsweep': 0.08726646259971647,
            'area_base':np.pi/4 * .29**2, 
        } 

        horizontal_tail_geometry = {
            'chord_root': 2.192842694642968,
            'wing_span': 6.741894864679805,
            'taper_ratio': 0.43,
            'diameter_fuselage': 0.,
            'chord_fraction_max_thickness': 0.3, 
            'pos_max_camber': 0.25, 
            'thickness_to_chord_ratio': .1 
        } 

        vertical_tail_geometry = {
            'chord_root': 2.7593115912126667,
            'wing_span': 2.81449782303691985,
            'taper_ratio': 0.7,
            'diameter_fuselage': 0.,
            'chord_fraction_max_thickness': 0.3,
            'pos_max_camber': 0.25, 
            'thickness_to_chord_ratio': .1 
        }

        IFtail = 1.04
        IFwing = 1.0
        IFfuselage = 1.0
        IFnacelle = 1.3 

        #imported landing gear data
        S_Anose = 0.17057  # m^2 (frontal area of nose gear)
        D_nose = 18*0.0254  # m tire diameter
        D_main = 33*0.0254  # m tire diameter
        W_nose = 4.25*0.0254  # m tire width
        W_main = 9.75*0.0254  # m tire width

        strut = 1.56  # m nose gear strut length #gear Y

        Nstrut = 1.56  # m nose gear strut length #gear Y

        main_gear_geometry = {
            'diameter_wheel': D_main,
            'width_wheel': W_main,
            'height_strut': strut,
            'width_strut':W_main/2,
            'height_total': D_main/2 + strut,
            'width_total': W_main*1.5
        }

        nose_gear_geometry = {
            'diameter_wheel': D_nose,
            'width_wheel': W_nose,
            'height_strut': Nstrut,
            'width_strut': (S_Anose - W_nose*D_nose) / Nstrut,
            'height_total': D_nose/2 + Nstrut,
            'width_total': (S_Anose - W_nose*D_nose) / Nstrut + W_nose
        }

        l_nacelle = 1.9 # [m]
        d_nacelle = 1.08 # [m]

        mach_cruise = .77
        altitude = 35000*.3048

        #===INDIVIDUAL COMPONENT CHECKS===
        fuselage = dcm.Fuselage(IFfuselage, fuselage_geometry, 0.05, 0.634e-5)
        assert np.isclose(fuselage.surface_wetted, 236.8289), fuselage.surface_wetted
        assert np.isclose(fuselage.form_factor(), 1.064383), fuselage.form_factor()
        #NOTE the reference initial value is getting 0.00190, close enough since it is an intial value
        assert np.isclose(fuselage.Cf(altitude, mach_cruise), 0.00175882), fuselage.Cf(altitude, mach_cruise)
        assert np.isclose(fuselage.CD0_contribution(altitude, mach_cruise), 0.00175882*1.064383)
        assert np.isclose(fuselage.drag_area_contribution(mach_cruise), 0.07635754), fuselage.drag_area_contribution(mach_cruise)

        wing = dcm.Planform(IFwing, wing_geometry, .1, 0.634e-5, 1.07)
        assert np.isclose(wing.surface_wetted, 1.07*2*(60.95340747566614 - 11.0758)), f"{wing.surface_wetted} vs {1.07*2*(60.95340747566614 - 11.0758)}"
        assert np.isclose(wing.form_factor(mach_cruise), 1.57044), wing.form_factor(mach_cruise) #NOTE: absent from the reference
        #NOTE lenient tolerance as we compare with the reference initia value
        assert np.isclose(wing.Cf(altitude, mach_cruise), 0.00236, rtol=1e-2), wing.Cf(altitude, mach_cruise) 
        assert np.isclose(wing.CD0_contribution(altitude, mach_cruise), 1.57044*0.00236, rtol=1e-2)

        horizontal_tail = dcm.Planform(IFtail, horizontal_tail_geometry, 0.1, 0.634e-5, 1.05)
        assert np.isclose(horizontal_tail.surface_wetted, 1.05*2*10.570481), horizontal_tail.surface_wetted
        
        vertical_tail = dcm.Planform(IFtail, vertical_tail_geometry, 0.1, 0.634e-5, 1.05)
        assert np.isclose(vertical_tail.surface_wetted, 1.05*2*6.6011611), vertical_tail.surface_wetted

        nose_landing_gear = dcm.LandingGear(nose_gear_geometry, False)
        assert np.isclose(nose_landing_gear.drag_area_contribution(mach_cruise), 0.3165262405), nose_landing_gear.drag_area_contribution(mach_cruise)

        nose_landing_gear = dcm.LandingGear(nose_gear_geometry, True)
        assert np.isclose(nose_landing_gear.drag_area_contribution(mach_cruise), 0.2943670274), nose_landing_gear.drag_area_contribution(mach_cruise)

        main_landig_gear = dcm.LandingGear(main_gear_geometry, False)
        
        nacelle = dcm.Bay(IFnacelle, l_nacelle, d_nacelle, 0.1, 0.634e-5)
        assert np.isclose(nacelle.surface_wetted, 2*np.pi/4*d_nacelle**2+np.pi*d_nacelle*l_nacelle), nacelle.surface_wetted
        assert np.isclose(nacelle.form_factor(mach_cruise), 1+.35/l_nacelle*d_nacelle), nacelle.form_factor(mach_cruise)

        #partial components list
        components = [
            fuselage,
            wing,
            nose_landing_gear
        ]
        surface_reference = wing.surface_wetted / 2 / 1.07

        CD0_ref_friction = (fuselage.CD0_contribution(altitude, mach_cruise)*fuselage.surface_wetted+wing.CD0_contribution(altitude, mach_cruise)*wing.surface_wetted)/(wing.surface_wetted+fuselage.surface_wetted)
        CD0_ref_area = (fuselage.drag_area_contribution(mach_cruise) + nose_landing_gear.drag_area_contribution(mach_cruise)) / surface_reference
        
        CD0_ref = CD0_ref_area + CD0_ref_friction
        CD0_no_leakage = dcm.estimate_CD0(components, altitude, mach_cruise, surface_reference, 0.)
        CD0_leakage = dcm.estimate_CD0(components, altitude, mach_cruise, surface_reference, 0.1)
        assert np.isclose(CD0_no_leakage/.9, CD0_leakage)

        assert np.isclose(CD0_no_leakage, CD0_ref), f"{CD0_no_leakage} vs ref {CD0_ref}"



        
        

