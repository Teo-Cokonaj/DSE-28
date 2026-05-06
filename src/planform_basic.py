from ISA import calcISA, ftMeters, flMeters
g = 9.81 #m/s^2, gravitational acceleration
# DAST ARW-2 given parameters
b_d = 5.79 #m
AR_d = 10.3
m_d = 1060 #kg

#DAST ARW-2 derived parameters
S_d = b_d**2/AR_d
W_over_S_d = m_d*g/S_d

# HUGO requirements
m_h = 50 #kg, mass of HUGO
AR_h = 23
W_over_S_h = 3000 #N/m^2, wing loading of HUGO

# HUGO derived parameters
S_h = m_h*g/W_over_S_h
b_h = (AR_h*S_h)**0.5

print('DAST ARW-2:\nWing span: ' + "%.2f" % b_d + ' m\nAspect Ratio: ' + "%.2f" % AR_d + '\nMass: ' + "%.2f" % m_d + ' kg\nWing area: ' + "%.2f" % S_d + ' m^2\nWing loading: ' + "%.2f" % W_over_S_d + ' N/m^2\n')
print('HUGO:\nWing span: ' + "%.2f" % b_h + ' m\nAspect Ratio: ' + "%.2f" % AR_h + '\nMass: ' + "%.2f" % m_h + ' kg\nWing area: ' + "%.2f" % S_h + ' m^2\nWing loading: ' + "%.2f" % W_over_S_d + ' N/m^2\n')