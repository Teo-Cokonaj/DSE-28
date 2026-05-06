# Parameters for altitude calculation for aproximating HUGO's operational flight level

gamma = 1.4 # From literature for air
g0 = 9.81 # Grav constant
R = 287.05 # Gas constant for air
M = 0.75 # Mach number from requirements
AR = 19 # Aspect ratio (between 19-27)
b = 6 # wing span from bullshit van sizings (between 6-15)
sfc = 0.153 /3600 # SFC for PBS TJ40-G1
E = 30 * 60 # Endurance from mission requirements
F_T = 410 # Approximate thrust for PBS TJ40-G1
Wi = 100 # Approximate MTOW
Wf = 60  # Approximate EOM
CL = 0.15 # Approximate CL from Lockheed X-56A
a = -6.5 * 10 ** (-3) # ISA parameter for the troposphere
T0 = 288.15 # Temperature at sea level in Kelvin
rho0 = 1.225 # Density at sea level in kgm^(-3)
p0 = 101325 # Pressure at sealevel in Pa
h0 = 0 # Da ground