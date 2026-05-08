# First try at using geometry from aerosandbox - Guilherme

import aerosandbox as asb
import aerosandbox.numpy as np


# This is for a non-parametric wing and tail (for now)


# Relevant Parameters

# Main Wing

    # @ Root

    # @ midway

    # @ tip

# Horizontal Stabilizer

    # @ Root

    # @ Tip

# Vertical Stabilizer

    # @ Root

    # @ Tip


# Control Surface Deflections:

    # Aileron Deflection

    # Elevetor Deflection

    # Rudder Deflection



# Select airfoils

    # Wing

wing_airfoil = asb.Airfoil('naca9999')

    # Tail

tain_airfoil = asb.Airfoil('naca0012')





airplane = asb.Airplane(


    name = "HUGO (infant)",


    xyz_ref = [0, 0, 0],


    wing = [

        asb.Wing(

            name = "main wing",
            xyz_le = [0, 0, 0],
            symmetric = True,
            xsecs = [

                asb.WingXSec(

                    xyz_le = [0, 0, 0],
                    chord = "",
                    twist = "",
                    airfoil = wing_airfoil,
                    control_surface_is_symmetric = True,
                    control_surface_deflection = 0,

                ),

                asb.WingXSec(

                    xyz_le = [],
                    chord = "",
                    twist = "",
                    airfoil = wing_airfoil,
                    control_surface_is_symmetric = True,
                    control_surface_deflection = 0,

                ),

                asb.WingXSec(

                    xyz_le = [],
                    chord = "",
                    twist = "",
                    airfoil = wing_airfoil,

                ),



            ],


        ),

    asb.Wing(

        name = "horizontal stabilizer",
        symmetric = True,
        xsecs = [
            asb.WingXSec(
                xyz_le = [],
                chord = "",
                twist = "",
                airfoil = tail_airfoil,
                control_surface_is_symmetric = True,
                control_surface_deflection = 0,

            ),
            asb.WingXSec(
                xyz_le = [],
                chord = "",
                twist = "",
                airfoil = tail_airfoil,

            ),

        ],

    ).translate(

        ["", "", ""]

    ),

    asb.WingXSec(
        name = "vertical stabilizer",
        symmetric = False,
        xsecs = [
            asb.WingXSec(
                xyz_le = [],
                chord = "",
                twist = "",
                airfoil = tail_airfoil,
                control_surface_is_symmetric = True,
                control_surface_deflection = 0,

            ),

            asb.WingXSec(
                xys_le = []
                chord = "",
                twist = "",
                airfoil = tail_airfoil,


            ),

        ],


    ).translate(
        
        ["", "", ""]
        
        ),

    ]

)


if __name__ == "__main__":
    airplane.draw_three_view()


    

        


