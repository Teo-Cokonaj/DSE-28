from ISA import calcISA, ftMeters, flMeters
# HUGO requirements
M_cr = 0.75
h_ft = 27000
# Air properties
gamma = 1.4
R = 287
#Parameters determined from DAST ARW-2
W_over_S = 3000
V_stall = 60 #m/s, stall speed at sea level

def get_C_L_des(M_cr, h_ft):
    T, p, rho = calcISA(ftMeters(h_ft))
    a = (gamma*R*T)**0.5
    V = M_cr*a
    q_inf = 0.5*rho*V**2
    C_L_des = W_over_S/q_inf
    return C_L_des

def get_C_L_stall(V_stall):
    rho0 = calcISA(0)[2]
    q_inf = 0.5*rho0*V_stall**2
    C_L_stall = W_over_S/q_inf
    return C_L_stall

print(get_C_L_des(M_cr, h_ft))
print(get_C_L_stall(V_stall))