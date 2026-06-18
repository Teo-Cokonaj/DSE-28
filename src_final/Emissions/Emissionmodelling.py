import numpy as np
import matplotlib.pyplot as plt
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from global_parameters import *

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
    def TotalEM(self,fuelflow):
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
    def TotalEMGWP(self,fuelflow):
        GWP=(CO2_per_fuel*CO2_GWP
        +H2O_per_fuel*H2O_GWP
        +NMVOCs_per_fuel*NMVOCs_GWP
        +SO42_per_fuel*SO42_GWP
        +CO_per_fuel*CO_GWP
        +Soot_per_fuel*Soot_GWP
        +Contrails_cirrusb_per_fuel*Contrails_cirrusb_GWP)*fuelflow
        return (GWP)


Emmis=Emmisions()
x=[]
y=[]
z=[]
print(Emmis.TotalEM(5.31045413298577/1500))

for i in range(0,1500,10):
    for j in range(0,5000,10):
            x.append(i)
            y.append(j)
            if (j>2000 and j<2500):
                z.append(Emmis.TotalEM(5.31045413298577/1500))
            else:
                z.append(0)
for i in range(1500,1800,10):
    for j in range(0,5000,10):
            x.append(i)
            y.append(j)
            if (j>3000 and j<3500):
                z.append(Emmis.TotalEM(1.111694622595013/300))
            else:
                z.append(0)
                
for i in range(1800,2280,10):
    for j in range(0,5000,10):
            x.append(i)
            y.append(j)
            if (j>1000 and j<1500):
                z.append(Emmis.TotalEM(1.8129882930851229/480))
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

def fuelflow(m_fuel,t):
    return (m_fuel/t)  

def plotGWP(m1,m2,m3,t1,t2,t3):
    x=[]
    y=[]
    fuelburnt=0
    for i in range(0,t1,1):
        x.append(i)
        fuelburnt=fuelburnt+5.31045413298577/1500
        y.append(fuelburnt)
    t=t1+1
    for i in range(t,t+t2,1):
        x.append(i)
        fuelburnt=fuelburnt+1.111694622595013/300
        y.append(fuelburnt)
    t=t+t2+1
    for i in range(t,t+t3,1):
        x.append(i)
        fuelburnt=fuelburnt+1.8129882930851229/480.0
        y.append(fuelburnt)    
    sc = plt.plot(x, y,color='blue')
    plt.xlabel('Time [s]')
    plt.ylabel('SPL [dB]')
    plt.ylim(0,15)
    plt.tight_layout()
    plt.show()
    print(np.sum(y)/8)
    print(np.sum(y)*5*1000*15)
    print(8*5*1000*15)
     
    


def run_self_tests():
    def assert_(condition, msg):
        if not condition:
            raise AssertionError(f"FAIL: {msg}")
        print(f"  OK  {msg}")
        
    EM=Emmisions()
    
    EM = Emmisions()
    f  = 1.0  

    #Zero fuelflow → zero output
    assert_(EM.TotalEM(0) == 0,      "zero fuelflow → zero mass")
    assert_(EM.TotalEMGWP(0) == 0,   "zero fuelflow → zero GWP")

    # double fuelflow → double output
    assert_(EM.TotalEM(2*f) == 2*EM.TotalEM(f),        "TotalEM linear in fuelflow")
    assert_(EM.TotalEMGWP(2*f) == 2*EM.TotalEMGWP(f),  "TotalEMGWP linear in fuelflow")


    #Sum of individual masses equals TotalEM
    mass_parts = EM.CO2(f)[0]+EM.H2O(f)[0]+EM.NMVOCs(f)[0]+EM.SO42(f)[0]+EM.CO(f)[0]+EM.Soot(f)[0]+ EM.Contrails_cirrusb(f)[0]
    assert_(abs(mass_parts - EM.TotalEM(f)) < 1e-10, "parts sum to TotalEM")

    #Sum of individual GWPs equals TotalEMGWP 
    gwp_parts = EM.CO2(f)[1]+EM.H2O(f)[1]+EM.NMVOCs(f)[1]+EM.SO42(f)[1]+EM.CO(f)[1]+EM.Soot(f)[1]+ EM.Contrails_cirrusb(f)[1]
    assert_(abs(gwp_parts - EM.TotalEMGWP(f)) < 1e-10, "parts GWP sum to TotalEMGWP")

    #SO42 cools (negative GWP) 
    assert_(EM.SO42(f)[1] < 0, "SO42 GWP is negative (cooling effect)")

    #CO2 GWP factor = 1
    assert_(abs(EM.CO2(f)[0] - EM.CO2(f)[1]) < 1e-10, "CO2: mass == GWP (factor=1)")

    assert_(EM.TotalEM(10) >
            EM.TotalEM(5), "High FF > LOW FF")
    assert_(EM.TotalEMGWP(10) >
            EM.TotalEMGWP(5), "High FF > LOW FF")   

    print("Running self-tests...")
    print("All tests passed.")


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        run_self_tests()
    else:
        plotGWP(5.31045413298577,1.111694622595013,1.8129882930851229,1500,300,480)

