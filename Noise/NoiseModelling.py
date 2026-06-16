import numpy as np
from ConstantsForNoisemodelling import *
import matplotlib.pyplot as plt
import aerosandbox 
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src_final.global_parameters import *


# Data taken from article Micro Turbojet Engine Nozzle Ejector Impact on the Acoustic Emission, Thrust Force and Fuel Consumption Analysis
# Data used for the polynomic regression can be found at:     
theta=0
phi=0
S_wing=2
b_wing=5
S_tail=0.2
b_tail=2
nu=CONSTANTS.DYNAMIC_VISCOSITY_SEA_LEVEL 
asm=Assumptions()


r=asm.altitude_cruise
atm =aerosandbox.Atmosphere(altitude=r)
V_mach_cruise=atm.speed_of_sound()*asm.mach_cruise
V_take_off=150/3.6
r=asm.altitude_mach_max
V_mach_max=atm.speed_of_sound()*asm.mach_max
V_landing=150/3.6*1.3

x=[]
y=[]
z=[]


class NoJet():
    def SPL_idle(f):  
        SPL_idle= -3.91307587961444e-45*f**12 + 4.35977721851869e-40*f**11 - 2.13212130367326e-35*f**10 + 6.01841967768376e-31*f**9 - 1.08501038521621e-26*f**8 + 1.30612122914030e-22*f**7 - 1.06686840247447e-18*f**6 + 5.89291155847126e-15*f**5 - 2.15219108643501e-11*f**4 + 4.93883702524919e-8*f**3 - 6.34355477112855e-5*f**2 + 3.13219879921222e-2*f + 63.558197122511
        return SPL_idle
    def SPL_cruise(f):
        SPL_cruise= -1.48979712368789e-52*f**14 + 2.08861070102091e-47*f**13 - 1.30971882498895e-42*f**12 + 4.84657305246113e-38*f**11 - 1.17579934893136e-33*f**10 + 1.96500667305387e-29*f**9 - 2.31366927411666e-25*f**8 + 1.92997979022625e-21*f**7 - 1.13167474636886e-17*f**6 + 4.56879559971655e-14*f**5 - 1.22550981367464e-10*f**4 + 2.06484328674429e-7*f**3 - 1.98965081796497e-4*f**2 + 8.75664063514000e-2*f + 62.8430095603916
        return SPL_cruise
    def SPL_max(f):
        SPL_max=-9.18936038328848e-53*f**14 + 1.25939275391289e-47*f**13 - 7.73289462711177e-43*f**12 + 2.80819422959747e-38*f**11 - 6.70602460844632e-34*f**10 + 1.10767753662943e-29*f**9 - 1.29623541267938e-25*f**8 + 1.08283960421850e-21*f**7 - 6.42519653058702e-18*f**6 + 2.66323800944127e-14*f**5 - 7.48798239695728e-11*f**4 + 1.36525938641541e-7*f**3 - 1.50941114946926e-4*f**2 + 8.80311321680095e-2*f + 69.0909644480236
        return SPL_max


#The noise assosiated to the fuselage 
class NoFusWing():   
    def __init__(self, S:float, b:float):
        self.WingSurface=S  
        self.span=b         
    def SPL(self,f,theta,V):
        delta=0.37*(self.WingSurface/self.span)*(V*self.WingSurface/self.span*nu)**(0.3)
        OASPL=50*np.log10(V/51.44)+10*np.log10(delta*self.span/(1**2)*(np.cos(phi)**2)*(np.cos(theta/2)**2))+101.3
        DeltaSPL=-0.03*(1/152.4)*(f/(0.1*V/delta)-1)**(3/2)
        SPL=OASPL+10*np.log10(0.613*(f/(0.1*V/delta))**4*((f/(0.1*V/delta))**(3/2)+0.5)**(-4))+DeltaSPL+6
        return SPL


class Noise(): 
    def __init__(self):
        self.Jet=NoJet()
    def SPL(self,f,S,b,theta,V,c,r):
        if c==0:
            NoJetSPL=NoJet.SPL_idle(f)+20*np.log10(1.2)    
        if c==1:
            NoJetSPL=NoJet.SPL_cruise(f)+20*np.log10(1.2)    
        if c==2:
            NoJetSPL=NoJet.SPL_max(f)+20*np.log10(1.2)  
            
        NoFusWingSPL=NoFusWing(S_wing,b_wing).SPL(f,theta,V)
        NoFusTailSPL=NoFusWing(S_tail,b_tail).SPL(f,theta,V)
        NoTurb=np.log10(2)+NoJetSPL
        SPL_total= 10*np.log10((10**(NoFusWingSPL/10)+10**(NoTurb/10)+10**(NoFusTailSPL/10)))+20*np.log10(1/r) 
        return(SPL_total)
        
  
    def plotFlyover(self,S,b,theta,V,c,r,d):
        x=[]
        y=[]
        z=[]
        r=asm.altitude_cruise
        atm =aerosandbox.Atmosphere(altitude=r)
        V=atm.speed_of_sound()*asm.mach_cruise
        V=V_mach_max
        for i in range(0,d,1):
            rit=r/(np.sin(np.pi/1000+i*np.pi/1.01/d))
            for f in range(200,15000,20):
                z.append(i-1000)
                x.append(f)
                Result=self.SPL(f,S,b,theta,V,2,rit)
                y.append(Result.real)
        
        plt.figure()
        sc = plt.scatter(z, x, c=y, cmap='magma', s=40,vmin=0, vmax=40)
        plt.colorbar(sc, label='SPL (in decibels)')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.tight_layout()
        plt.show()
        return ("done")
        

    def plotOperation(self,S,b,theta):
        x=[]
        y=[]
        z=[]
        def FlightProfile(c1,c2,t,V1,V2):
            for f in range(200,15000,20):
                        z.append(i)
                        x.append(f)
                        if (i<=t+200 and t<=i):
                            Result=self.SPL(f,S,b,theta,V1,c1,r)*(1-(i-t)/200)+self.SPL(f,S,b,theta,V2,c2,r)*(((i-t)/200))
                        else:
                            Result=self.SPL(f,S,b,theta,V2,c2,r)
                            
                        y.append(Result.real)
            return ("fisk")
        
        t=1000
     
        #take-off
        for i in range(0,t,1):
            V=150/3.6+0.9*V_mach_cruise/1000*i
            r=10+asm.altitude_cruise/t*i
            for f in range(200,15000,20):
                z.append(i)
                x.append(f)
                Result=self.SPL(f,S,b,theta,V,2,r)
                y.append(Result.real)
       

       #cruise first phase 
        t=t+1
        for i in range(t,int(t+asm.time_cruise/2),1):
            r=asm.altitude_cruise
            atm =aerosandbox.Atmosphere(altitude=r)
            V=atm.speed_of_sound()*asm.mach_cruise
            FlightProfile(2,1,t,150/3.6+0.9*V_mach_cruise,V_mach_cruise)

        
        #Max cruise
        t=t+int(asm.time_cruise/2)+1
        print(t)
        for i in range(t,int(t+asm.time_mach_max),1):
            r=asm.altitude_mach_max
            atm = aerosandbox.Atmosphere(altitude=r)
            V=atm.speed_of_sound()*asm.mach_max
            FlightProfile(1,2,t,V_mach_cruise,V_mach_max)

        t=t+1+int(asm.time_mach_max)       
        
        #cruise second phase 
        for i in range(t,int(t+asm.time_cruise/2),1):
            r=asm.altitude_cruise
            atm = aerosandbox.Atmosphere(altitude=r)
            V=atm.speed_of_sound()*asm.mach_cruise
            FlightProfile(2,1,t,V_mach_max,V_mach_cruise)

        t=t+1+int(asm.time_cruise/2)

        #Landing approach 
        for i in range(t,t+400,1):
            r=100+asm.altitude_cruise*(1-(i-t)/400)
            V=150/3.6*1.3
            FlightProfile(1,0,t,V_mach_cruise,V_landing)
        
        
        plt.figure()
        sc = plt.scatter(z, x, c=y, cmap='viridis', s=10,vmin=0, vmax=60)
        plt.colorbar(sc, label='SPL (in decibels)')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.tight_layout()
        plt.show()
        return ("done")
        
       
                
        
noise = Noise()
noise.plotFlyover(S,b,theta,V_mach_max,2,1000,2000)
#noise.plotOperation(S,b,theta)



