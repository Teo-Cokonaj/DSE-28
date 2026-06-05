import control.matlab as ml
import numpy as np
import matplotlib.pyplot as plt

#m = input("Enter the Maximum Take Off Weight:")
#L = input("Enter the lift at landing:")

def landing_gear_response(k:float, 
                          c:float, 
                          downward_landing_speed:float = 15,                    # Has to be implemented into simulation, but I am not sure how to do that using lsim
                          displacement_constraint_compression:float = 0.0095, 
                          force_requirement: float = 4, 
                          dt:float = 0.01, 
                          t:int = 5, 
                          m:float = 50, 
                          L:float = 35, 
                          plotting:bool = False, 
                          debug:bool = False):

    # defining units

    # k                                     [N/m]
    # c                                     [Pa/m/s]
    # landing_speed                         [m/s]
    # displacement_constraint_compression   [m]
    # force requirement (how many g)        [-]
    # dt                                    [s]
    # t                                     [s]
    # m                                     [kg]
    # L                                     [N]



    # constants

    g = 9.80665                             # [m/s/s]

    # state space matrices

    A = [ [0, 1], [-k/m, -c/m] ]        # simple model of spring and dashpot in paralel

    B = [0, 1]                          # one input in x2

    C = [[1, 0], [k, c]]                # First row, tracks displacement of landing gear, second row tracks force applied
                                        # The constraint on the displacement is 0.95cm as stated by Alex, and 4g on the force as determined by CS-23 requirements 
    D = [[0], [0]]

    # creation of a state space
    state_space = ml.ss(A, B, C, D)
    MIMO_transfer_function = ml.tf(state_space)

    # decomposition of MIMO TF to SISO
    SISO_TF_displacement = MIMO_transfer_function[0, 0]
    SISO_TF_force = MIMO_transfer_function[1,0]

    #_____________________________________________Simulating step response of landing gear:_____________________________________________________________________________

    max_load = g - L/m                                                                                  # load applied [N]
    
    load_requirement = force_requirement * m * g                                                        # [N]              

    t = np.arange(0, t + dt, dt)                                                                        # time array

    inp = max_load * np.ones_like(t)                                                                    # input step array


    # TO DO!!!!! implement X0 as downward velocity component (x2 in the sate vector)
    y_displacement, T_displacement, x_displacement = ml.lsim(SISO_TF_displacement, inp, T=t )           # step response of displacement

    y_force, T_force, x_force = ml.lsim(SISO_TF_force, inp, T=t)                                        # step response of force

    # constraints of displacement response
    y_displacement_constraint_compression = displacement_constraint_compression * 100 * np.ones_like(t)       

    # constraints of force response

    y_force_constraint_compression = force_requirement * g * m / 1000 * np.ones_like(t) 

    #___________________________________________________________________________________________________________________________________________________________________



    # plotting

    if plotting:
        fig, axs = plt.subplots(1, 2)                                                                       # subplots

        # plotting response

        # displacement plotting

        axs[0].plot(t, 
                    y_displacement * 100,  
                    color='steelblue', 
                    label="Displacement")
        axs[0].plot(t, 
                    y_displacement_constraint_compression, 
                    'r--',  
                    label=f"Compression limit ({displacement_constraint_compression*100:.2f} cm)")
        axs[0].set_title("Displacement Response")
        axs[0].set_xlabel("Time (s)")
        axs[0].set_ylabel("Displacement (cm)")
        axs[0].legend()
        axs[0].grid(True)

        # force plotting

        axs[1].plot(t, 
                    y_force / 1000, 
                    color='darkorange', 
                    label="Gear force")
        axs[1].plot(t, 
                    y_force_constraint_compression, 
                    'r--', 
                    label="4g limit")
        axs[1].set_title("Force Response")
        axs[1].set_xlabel("Time (s)")
        axs[1].set_ylabel("Force (kN)")
        axs[1].legend()
        axs[1].grid(True)

        plt.tight_layout()
        plt.show()

    # constraints met?

    peak_displacement = np.max(np.abs(y_displacement)) * 100
    peak_force = np.max(np.abs(y_force)) / 1000

    met_displacement_constraints = peak_displacement < np.abs(displacement_constraint_compression) * 100 
    met_force_constraints = peak_force < load_requirement / 1000

    constraints_met = False


    if met_displacement_constraints:
        if met_force_constraints:
            constraints_met = True
        else:
            print("Failed to meet force constraints")

    else:
        print("Failed to meet displacement constraints")


    # debugging
    if debug:
        print("MIMO TF from state space (two transfer functions expected with same denominator): ", MIMO_transfer_function)
        print("SISO TF of displacement: ", SISO_TF_displacement)
        print("SISO TF of force", SISO_TF_force)

    return y_displacement, y_force, constraints_met


if __name__ == "__main__":
    K = 100000
    C = 120

    y_displacement, y_force, constraints_met = landing_gear_response(K, C, plotting = True, debug = True)

    y_disp_max = np.max(np.abs(y_displacement))
    y_force_max = np.max(np.abs(y_force))

    print("max displacement: ", y_disp_max * 100, " [cm]")
    print("max force: ", y_force_max / 1000, " [kN]")

    print("The constraints were met: ", constraints_met)


