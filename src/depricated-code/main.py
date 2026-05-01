from flight_level import density_temp, altitude_determination
from parameters_for_altitude import *



S = b**2/AR

rt = density_temp(M, gamma, R, S, CL, g0, sfc, E, F_T, Wi, Wf)

h = altitude_determination(rt, p0, T0, a, h0, R, gamma, g0)

print(h)