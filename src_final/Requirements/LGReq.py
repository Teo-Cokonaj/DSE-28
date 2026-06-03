import sys
import os
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src_final.Requirements.Requirement import Requirement
from Aircraft.Aircraft import Aircraft


class LGReq(Requirement):
    def assess(self, aircraft:Aircraft) -> bool:
    

        x_main_lg = aircraft.fixed.x_main_gear
        x_cg = aircraft.fixed.x_cg_max
        x_tail_cone = aircraft.fixed.x_tail_cone # add to fixed class
        x_nose_lg = aircraft.fixed.x_nose_gear

        y_wing_span = aircraft.planforms.span
        y_main_lg = aircraft.fixed.main_gear

        z_cg = aircraft.fixed.z_cg
        z_tail_cone = aircraft.fixed.z_tail_cone # add to fixed class
        z_wing = aircraft.fixed.z_wing # add to fixed class

        # scrape angle (theta ~= 15 degrees)

        # in radians
        theta = np.arctan( z_tail_cone / ( x_tail_cone - x_main_lg ) )

        theta_degrees = theta * 180 / np.pi
        

        # beta angle ( beta > theta)

        beta = np.arctan( (x_main_lg - x_cg) / z_cg)
        beta_degrees = beta * 180 / np.pi

        # tip over cg (psi < 55 degrees)

        psi = np.arctan( z_cg / ((x_cg - x_nose_lg) * np.sin( np.arctan ( y_main_lg / (x_main_lg - x_nose_lg)))))
        psi_degrees = psi * 180 / np.pi

        # wing strike ( )

        phi = np.arctan( z_wing / ( (y_wing_span - y_main_lg) * 0.5) )
        phi_degrees = phi * 180 / np.pi



        # Truth Table:

        theta_pass = 14 < theta_degrees < 16
        beta_pass = beta_degrees > theta_degrees
        psi_pass = psi_degrees < 55
        phi_pass = phi_degrees > 8 


        if theta_pass:
            if beta_pass:
                if psi_pass:
                    if phi_pass:
                        print('all constraints satisfied')
            
                    else:
                        print('phi fails')
                else:
                    print('psi fails')
            else:
                print('beta_fails')
        else:
            print('theta fails')

        return theta_pass and beta_pass and psi_pass and phi_pass



                    
                        



        
        