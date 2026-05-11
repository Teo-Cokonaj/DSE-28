import aerosandbox as asb
import aerosandbox.numpy as np
import sys
import os
from typing import Optional
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from objects.lifting_surface_planform import LiftingSurfacePlanform
from objects.aircraft_parameters import AircraftParameters
import ac_params as acp

def calculate_LE_x_positions(number_of_sections: int,
                           planform: LiftingSurfacePlanform):
    return np.linspace(0.0,planform.half_span*np.tan(planform.sweep_LE_rad),number_of_sections)


def calculate_section_y_positions(number_of_sections: int,
                           planform: LiftingSurfacePlanform):
    return np.linspace(0.0,planform.half_span,number_of_sections)


def make_horizontal_lifting_surface(
    planform: LiftingSurfacePlanform,
    number_of_sections: int,
    twists: np.ndarray,
    airfoils: np.ndarray,
) -> asb.Wing:

    xsecs = []

    section_LE_x_positions=calculate_LE_x_positions(number_of_sections,planform)
    section_y_positions = calculate_section_y_positions(number_of_sections,planform)

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


def make_vertical_lifting_surface(
    planform: LiftingSurfacePlanform,
    number_of_sections: int,
    twists: np.ndarray,
    airfoils: np.ndarray,
) -> asb.Wing:

    xsecs = []

    section_LE_x_positions=calculate_LE_x_positions(number_of_sections,planform)
    section_y_positions = calculate_section_y_positions(number_of_sections,planform)

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

def make_airplane_model(aircraft_parameters: AircraftParameters,
                        wing_planform: LiftingSurfacePlanform,
                        horizontal_stabilizer_planform: LiftingSurfacePlanform,
                        vertical_stabilizer_planform: LiftingSurfacePlanform,
                        wing_number_of_sections: int,
                        wing_airfoils: np.ndarray,
                        horizontal_stabilizer_number_of_sections: int,
                        horizontal_stabilizer_airfoils: np.ndarray,
                        vertical_stabilizer_number_of_sections: int,
                        vertical_stabilizer_airfoils: np.ndarray,
                        canard_planform: Optional[LiftingSurfacePlanform] = None,
                        canard_number_of_sections: Optional[int] = None,
                        canard_airfoils: Optional[np.ndarray] = None,
                        ):


    main_wing=make_horizontal_lifting_surface(wing_planform,
                                              wing_number_of_sections,
                                              twists=np.linspace(0.0,wing_planform.tip_twist,wing_number_of_sections),
                                              airfoils=wing_airfoils)
    
    horizontal_stabilizer=make_horizontal_lifting_surface(horizontal_stabilizer_planform,
                                                          horizontal_stabilizer_number_of_sections,
                                                          twists=np.linspace(0.0,
                                                                             horizontal_stabilizer_planform.tip_twist,
                                                                             horizontal_stabilizer_number_of_sections),
                                                          airfoils=horizontal_stabilizer_airfoils
    ).translate([aircraft_parameters.horizontal_stabilizer_distance_from_wing,0.0,0.0])

    #Vertical tail assumed to have no twist!
    vertical_stabilizer=make_vertical_lifting_surface(vertical_stabilizer_planform,
                                                          vertical_stabilizer_number_of_sections,
                                                          twists=np.linspace(0.0,0.0,vertical_stabilizer_number_of_sections),
                                                          airfoils=vertical_stabilizer_airfoils
    ).translate([aircraft_parameters.vertical_stabilizer_distance_from_wing,0.0,0.0])

    if (canard_planform is not None) and (canard_number_of_sections is not None) and (canard_airfoils is not None):
        canard=make_horizontal_lifting_surface(canard_planform,
                                            canard_number_of_sections,
                                            twists=np.linspace(0.0,
                                                                canard_planform.tip_twist,
                                                                canard_number_of_sections),
                                            airfoils=canard_airfoils).translate(
                                                [-aircraft_parameters.canard_distance_in_front_of_wing,0.0,0.0]
                                                )

        airplane = asb.Airplane(
        name="HUGO",
        xyz_ref=[0.0, 0.0, 0.0],  # Change to CG location!!!
        wings=[ main_wing,
                horizontal_stabilizer,
                vertical_stabilizer,
                canard
        ],
    )
        
    else:
        airplane = asb.Airplane(
        name="HUGO",
        xyz_ref=[0.0, 0.0, 0.0],  # Change to CG location!!!
        wings=[ main_wing,
                horizontal_stabilizer,
                vertical_stabilizer,
        ],
    )

    return airplane

if __name__ == "__main__":
    aircraft_parameters=AircraftParameters(total_mass=acp.m_HUGO,
                                           horizontal_stabilizer_distance_from_wing=acp.horizontal_stabilizer_distance_from_wing_HUGO,
                                           vertical_stabilizer_distance_from_wing=acp.vertical_stabilizer_distance_from_wing_HUGO,
                                           canard_distance_in_front_of_wing=acp.canard_distance_in_front_of_wing)
    
    wing_planform=LiftingSurfacePlanform(aspect_ratio=acp.AR_HUGO,
                                span=acp.b_HUGO,
                                sweep_quarter_deg=acp.Lambda_qc_HUGO,
                                taper=acp.lambda_HUGO,
                                tip_twist_rad=acp.tip_twist_HUGO)
    
    horizontal_stabilizer_planform=LiftingSurfacePlanform(aspect_ratio=acp.HT_AR_HUGO,
                                                                span=acp.HT_span_HUGO,
                                                                sweep_quarter_deg=acp.HT_sweep_quarter_deg_HUGO,
                                                                taper=acp.HT_taper_HUGO,
                                                                tip_twist_rad=acp.HT_tip_twist_rad_HUGO)
    
    vertical_stabilizer_planform=LiftingSurfacePlanform(aspect_ratio=acp.VT_AR_HUGO,
                                                                span=acp.VT_span_HUGO,
                                                                sweep_quarter_deg=acp.VT_sweep_quarter_deg_HUGO,
                                                                taper=acp.VT_taper_HUGO,
                                                                tip_twist_rad=acp.VT_tip_twist_rad_HUGO)
    canard_planform=LiftingSurfacePlanform(aspect_ratio=acp.CN_AR_HUGO,
                                                                span=acp.CN_span_HUGO,
                                                                sweep_quarter_deg=acp.CN_sweep_quarter_deg_HUGO,
                                                                taper=acp.CN_taper_HUGO,
                                                                tip_twist_rad=acp.CN_tip_twist_rad_HUGO)

    wing_number_of_sections=100
    horizontal_stabilizer_number_of_sections=5
    vertical_stabilizer_number_of_sections=5
    canard_number_of_sections = 5

    wing_airfoil = asb.Airfoil('naca9999')
    tail_airfoil = asb.Airfoil('naca0012')
    canard_airfoil=asb.Airfoil('naca0012')

    wing_airfoils=np.array([wing_airfoil]*wing_number_of_sections)
    horizontal_stabilizer_airfoils=np.array([tail_airfoil]*horizontal_stabilizer_number_of_sections)
    vertical_stabilizer_airfoils=np.array([tail_airfoil]*vertical_stabilizer_number_of_sections)
    canard_airfoils=np.array([canard_airfoil]*canard_number_of_sections)

    airplane=make_airplane_model(aircraft_parameters,
                                 wing_planform,
                                 horizontal_stabilizer_planform,
                                 vertical_stabilizer_planform,
                                 wing_number_of_sections,
                                 wing_airfoils,
                                 horizontal_stabilizer_number_of_sections,
                                 horizontal_stabilizer_airfoils,
                                 vertical_stabilizer_number_of_sections,
                                 vertical_stabilizer_airfoils,
                                 canard_planform,
                                 canard_number_of_sections,
                                 canard_airfoils)
    
    airplane.draw_three_view()