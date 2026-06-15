import control.matlab as ml
import numpy as np
import matplotlib.pyplot as plt

#m = input("Enter the Maximum Take Off Weight:")
#L = input("Enter the lift at landing:")

def landing_gear_response(k:float, 
                          c:float, 
                          downward_landing_speed:float = 3,                    # Has to be implemented into simulation, but I am not sure how to do that using lsim
                          displacement_constraint_compression:float = 0.0775, 
                          dt:float = 0.01, 
                          t:int = 5, 
                          m:float = 50, 
                          plotting:bool = False, 
                          debug:bool = False):

    # defining units

    # k                                     [N/m]
    # c                                     [Pa/m/s]
    # landing_speed                         [m/s]
    # displacement_constraint_compression   [m]
    # dt                                    [s]
    # t                                     [s]
    # m                                     [kg]
    # L                                     [N]



    # constants

    g = 9.80665                             # [m/s/s]

    L = m * g

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

    t = np.arange(0, t + dt, dt)                                                                        # time array

    inp = max_load * np.ones_like(t)                                                                    # input step array


    # TO DO!!!!! implement X0 as downward velocity component (x2 in the sate vector)
    #y_displacement, T_displacement, x_displacement = ml.lsim(SISO_TF_displacement, inp, T=t)           # step response of displacement

    #y_force, T_force, x_force = ml.lsim(SISO_TF_force, inp, T=t)                                       # step response of force

    y, T, x = ml.lsim(state_space, inp, T=t, X0=[0, downward_landing_speed])
    y_displacement = y[:, 0]         
    y_force        = y[:, 1]     
    
    # constraints of displacement response
    y_displacement_constraint_compression = displacement_constraint_compression * 100 * np.ones_like(t)       

    # peak force (sized for 1.5x mass already applied via m parameter)
    peak_force = np.max(np.abs(y_force))
    design_force = peak_force

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
        axs[1].axhline(design_force / 1000,
                    color='r',
                    linestyle='--',
                    label=f"Max gear force: {design_force/1000:.2f} kN")
        axs[1].set_title("Force Response")
        axs[1].set_xlabel("Time (s)")
        axs[1].set_ylabel("Force (kN)")
        axs[1].legend()
        axs[1].grid(True)

        plt.tight_layout()
        plt.show()

    # constraints met?

    peak_displacement = np.max(np.abs(y_displacement)) 

    met_displacement_constraints = peak_displacement < np.abs(displacement_constraint_compression) 

    constraints_met = False
    force_constraint = False
    displacement_constraint = False

    constraint_status = 0


    total_gs = peak_force * 1.5 / (m * g)


# debugging and constraint status evaluation

    met_displacement_constraints = peak_displacement < np.abs(displacement_constraint_compression) 

    # Determine constraint status based on your truth table
    # if met_displacement_constraints and met_force_constraints:
    #                                                                                                                                 # Both met: Check if system is overdamped (c^2 >= 4*m*k)
    #     if (c ** 2) >= (4 * m * k):
    #         constraint_status = 4  
    #                                                                                                         # Overdamped / invalid
    #     else:
    #         constraint_status = 3  
    #                                                                                                          # Both constraints met (underdamped)
    # elif met_displacement_constraints and not met_force_constraints:
    #     constraint_status = 1        
    #                                                                                                    # Only displacement constraint met
    # elif not met_displacement_constraints and met_force_constraints:
    #     constraint_status = 2    
    #                                                                                                        # Only force constraint met
    # else:
    #     constraint_status = 0                                                                                                       # Neither constraint met


# landing gear requirements HOT FIX
    if met_displacement_constraints:
        if (c ** 2) >= (4 * m * k):
            constraint_status = 2  # Overdamped / invalid
        else:
            constraint_status = 1  # Displacement constraint met (underdamped)
    else:
        constraint_status = 0  # Displacement constraint not met



    if debug:
        labels = {
             0: "Displacement constraint not met",
             1: "Displacement constraint met (Underdamped)",
             2: "Overdamped / Invalid",
        }

    # Return the status integer instead of the old boolean
    return y_displacement, y_force, constraint_status, design_force, total_gs


if __name__ == "__main__":
    K = 6590.07
    C = 1146.48

    # K = 48168.2
    # C = 781.115

    # K = 11066.2
    # C = 1404.13

    # K = 28895.5
    # C = 906.175

    V = 1
    m = 50

    y_displacement, y_force, constraint_status, design_force, total_gs = landing_gear_response(K, C, downward_landing_speed = V, m=m, plotting=True, debug=False)

    print("max displacement: ", np.max(np.abs(y_displacement)) * 100, " [cm]")
    print("max force (raw): ", np.max(np.abs(y_force)) / 1000, " [kN]")
    print("design force (1.5x safety factor): ", design_force / 1000, " [kN]")
    print("Constraint status: ", constraint_status)
    print("gs on fuselage (w/ SF: 1.5): ", total_gs , " [g]")

    y_disp_max = np.max(np.abs(y_displacement))
    y_force_max = np.max(np.abs(y_force))

    # print("max displacement: ", y_disp_max * 100, " [cm]")
    # print("max force: ", y_force_max / 1000, " [kN]")

    # print("The constraints were met: ", constraint_status)
