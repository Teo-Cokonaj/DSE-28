# Functions for Altitude from engine parameters

#from parameters_for_altitude import *
import numpy as np

 
def density_temp(M, gamma, R, S, CL, g, sfc, E, F_T, Wi, Wf): 
    
    #rt = np.array() #brother why array
    rt = 2/(M**2 * gamma * R * S * CL) * (g * sfc * E * F_T * np.log(Wi/Wf)) 

    return rt


def altitude_determination(rt, p0, T0, a, h0, R, gamma, g0):

    h = h0 + T0/a * ( (rt/p0)**((a*R)/(-g0)) - 1 )


    return h

