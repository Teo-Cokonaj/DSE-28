# Adam's version of the 1st year ISA calc
from math import e
gradients = [-0.0065, 0, 0.0010, 0.0028, 0, -0.0028, -0.0020]
altitudes = [11000, 20000, 32000, 47000, 51000, 71000, 86000]
g_0, T_0, p_0, rho_0, R = 9.80665, 288.15, 101325, 1.225, 287.0528

def inputErr(point):
    print('Input error at: "' + str(point) + '". Exitting')
    exit()
"""
print('--- ISA Calculator ---\n1. Calculate ISA for input in [m] \n2. Calculate ISA for input in [ft] \n3. Calculate ISA for input in [FL] \n')
try:
    choice = int(input('Select your choice: '))
except ValueError:
    inputErr('option selection')

if(choice < 1 or choice > 3):
inputErr('option selection')

try:
    altitude = float(input('Enter altitude: '))
except ValueError:
    inputErr('altitude input')

if(altitude < 0):
    inputErr('altitude input')
"""
def calcISA(alt):
    T, t_0 = T_0, T_0 #local variable
    p = p_0
    for i in range(0, len(altitudes)):
        if(alt > altitudes[i]):
            T += gradients[i]*(altitudes[i]-altitudes[i-1]) if i > 0 else gradients[i]*(altitudes[i])
            p *= pow(T/t_0,-g_0/(gradients[i] * R)) if gradients[i] != 0 else pow(e,((-g_0)/(R*T))*(altitudes[i]-altitudes[i-1])) #no need to check whether i is higher than 0 since the isothermal region is always at i > 0
            t_0 = T
        else:
            T += gradients[i]*(alt-altitudes[i-1]) if i > 0 else gradients[i]*alt
            p = p*pow(T/t_0,-g_0/(gradients[i] * R)) if gradients[i] != 0 else p*pow(e,((-g_0)/(R*T))*(alt-altitudes[i-1]))         
            break
    rho = p/(R*T)
    return T, p, rho

def ftMeters(feet):
    return float(0.3048 * feet)

def flMeters(fl):
    return float(0.3048 * 100 * fl)
""""
temp, pressure, density = calcISA(altitude) if choice == 1 else calcISA(ftMeters(altitude)) if choice == 2 else calcISA(flMeters(altitude))
print('\nTemperature: ' + "%.2f" % temp + ' [K]\n' + 'Pressure: ' + "%.2f" % pressure + ' [Pa]\n' + 'Density: ' + "%.2f" % density + ' [kg/m^3]\n') #print to 2 decimal points
"""