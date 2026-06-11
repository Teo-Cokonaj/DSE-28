import numpy as np
import matplotlib.pyplot as plt
import aerosandbox 
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src_final.global_parameters import *

CO2_per_fuel=3.16
H2O_per_fuel=1.23
NMVOCs_per_fuel=0.38*10**(-3)
SO42_per_fuel=6.54*10**(-7)
CO_per_fuel=0.003
Soot_per_fuel=0.03*10**(-3)
Contrails_cirrusb_per_fuel=3.16

CO2_GWP=1
H2O_GWP=0.22
NMVOCs_GWP=14.0
SO42_GWP=-832
CO_GWP=9
Soot_GWP=4288
Contrails_cirrusb_GWP=2.32

class Emmisions():
    def __init__(self):
        pass
    def CO2(self,fuelflow):
        return (CO2_per_fuel*fuelflow,CO2_GWP*CO2_per_fuel*fuelflow)
    def H2O(self,fuelflow):
        return (H2O_per_fuel*fuelflow,CO2_GWP*H2O_per_fuel*fuelflow)
    def NMVOCs(self,fuelflow):
        return (NMVOCs_per_fuel*fuelflow,NMVOCs_GWP*NMVOCs_per_fuel*fuelflow)  
    def SO42(self,fuelflow):
        return (SO42_per_fuel*fuelflow,SO42_GWP*SO42_per_fuel*fuelflow)
    def CO(self,fuelflow):
        return (CO_per_fuel*fuelflow,CO_GWP*CO_per_fuel*fuelflow)
    def Soot(self,fuelflow):
        return (Soot_per_fuel*fuelflow,Soot_GWP*Soot_per_fuel*fuelflow)
    def Contrails_cirrusb(self,fuelflow):
        return (Contrails_cirrusb_per_fuel*fuelflow,Contrails_cirrusb_GWP*Contrails_cirrusb_per_fuel*fuelflow)
    def Total(self,fuelflow):
        mass=(CO2_per_fuel
        +H2O_per_fuel
        +NMVOCs_per_fuel
        +SO42_per_fuel
        +CO_per_fuel
        +Soot_per_fuel
        +Contrails_cirrusb_per_fuel)*fuelflow
        GWP=(CO2_per_fuel*CO2_GWP
        +H2O_per_fuel*H2O_GWP
        +NMVOCs_per_fuel*NMVOCs_GWP
        +SO42_per_fuel*SO42_GWP
        +CO_per_fuel*CO_GWP
        +Soot_per_fuel*Soot_GWP
        +Contrails_cirrusb_per_fuel*Contrails_cirrusb_GWP)*fuelflow
        return (mass)

Emmis=Emmisions()
x=[]
y=[]
z=[]
print(Emmis.Total(5.31045413298577/1500))

for i in range(0,1500,10):
    for j in range(0,5000,10):
            x.append(i)
            y.append(j)
            if (j>2000 and j<2500):
                z.append(Emmis.Total(5.31045413298577/1500))
            else:
                z.append(0)
for i in range(1500,1800,10):
    for j in range(0,5000,10):
            x.append(i)
            y.append(j)
            if (j>3000 and j<3500):
                z.append(Emmis.Total(1.111694622595013/300))
            else:
                z.append(0)
                
for i in range(1800,2280,10):
    for j in range(0,5000,10):
            x.append(i)
            y.append(j)
            if (j>1000 and j<1500):
                z.append(Emmis.Total(1.8129882930851229/480))
            else:
                z.append(0)
        
        
        
plt.figure()
sc = plt.scatter(x, y, c=z, cmap='viridis', s=10,vmin=0, vmax=0.03)
plt.colorbar(sc, label='GWP')
plt.xlabel('x')
plt.ylabel('y')
plt.tight_layout()
plt.show()



"""
Fuel mass at cruise (8229.6 m, 1500 s) = 5.31045413298577 kg
Fuel mass at mach max (8229.6 m, 300) = 1.111694622595013 kg
Fuel mass at go-around (457.20000000000005 m, 480.0) = 1.8129882930851229 kg
"""