import numpy as np
from ConstantsForNoisemodelling import *
import matplotlib.pyplot as plt
import aerosandbox 
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src_final.global_parameters import *


# Data taken from article Micro Turbojet Engine Nozzle Ejector Impact on the Acoustic Emission, Thrust Force and Fuel Consumption Analysis
# Data used for the polynomic regression can be found at: the github folder under the name      
theta=0
phi=0
S_wing=0.439
b_wing=3.2
S_tail=0.086
b_tail=0.5701744594787047
nu=CONSTANTS.DYNAMIC_VISCOSITY_SEA_LEVEL 
asm=Assumptions()


r=asm.altitude_cruise
atm =aerosandbox.Atmosphere(altitude=r)
V_mach_cruise=atm.speed_of_sound()*asm.mach_cruise


V_take_off=40.49

r=asm.altitude_mach_max
print(asm.altitude_mach_max)
atm = aerosandbox.Atmosphere(altitude=r)
V_mach_max=atm.speed_of_sound()*asm.mach_max


V_landing=40.49*1.3
V_goaround=47.051


#A-filtering 

def R(f):
    R=12194**2*f**4/((f**2+20.6**2)*np.sqrt((f**2+107.7**2)*(f**2+737.9**2))*(f**2+1214**2))
    return R

def A_curve(f):
    return (20*np.log10(R(f))-20*np.log10(R(1000)))


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
    def SPL(self,f,theta,V,h):
        delta=0.37*(self.WingSurface/self.span)*(V*self.WingSurface/(self.span*nu))**(-0.2)
        OASPL=50*np.log10(V/51.44)+10*np.log10(delta*self.span/(h**2)*(np.cos(phi)**2)*(np.cos(theta/2)**2))+101.3
        DeltaSPL=-0.03*(1/152.4)*(f/(0.1*V/delta)-1)**(3/2)
        SPL=OASPL+10*np.log10(0.613*(f/(0.1*V/delta))**4*((f/(0.1*V/delta))**(3/2)+0.5)**(-4))+DeltaSPL
        return SPL
        
class Noise(): 
    def __init__(self):
        self.Jet=NoJet()
    def SPL(self,f,S,b,St,bt,theta,V,c,r):
        if c==0:
            NoJetSPL=NoJet.SPL_idle(f)+20*np.log10(1.2)    
        if c==1:
            NoJetSPL=NoJet.SPL_cruise(f)+20*np.log10(1.2)    
        if c==2:
            NoJetSPL=NoJet.SPL_max(f)+20*np.log10(1.2)  
            
        
        NoFusWingSPL=NoFusWing(S,b).SPL(f,theta,V,r)
        NoFusTailSPL=NoFusWing(St,bt).SPL(f,theta,V,r)
        #Make the jet noise for two jet turbines
        NoTurb=10*np.log10(2)*1+NoJetSPL
        #Adding all the sources of sound. Adding the inverse square law and A-filtering
        SPL_total= 10*np.log10(10**(NoFusTailSPL/10)+10**(NoFusWingSPL/10)+10**(NoTurb/10))+20*np.log10(1/r)+A_curve(f)-3
        return(SPL_total)
        
        
    #The function used to calculate the noise generated when the plane performs a flyover.
    def plotFlyover(self,S_wing,b_wing,S_tail,b_tail,theta,V,c,r,d,step):
        x=[]
        y=[]
        z=[]
        TotalT=[]
        TotalN=[]

        for i in range(0,d,step):
            fsum=0
            theta=0.0001+i*np.pi/d
            rit=r/(np.sin(theta))
            for f in range(150,15000,20):
                z.append(i-d)
                x.append(f)
                Result=self.SPL(f,S_wing,b_wing,S_tail,b_tail,theta,V,2,rit)
                y.append(Result.real)
                fsum=fsum+10*10**(Result/10)
            total=10*np.log10(fsum) 
            TotalN.append(total)
            TotalT.append(i-d)
        plt.figure()
        sc = plt.scatter(z, x, c=y, cmap='plasma', s=40,vmin=0, vmax=30)
        plt.colorbar(sc, label='SPL (in decibels)')
        plt.xlabel('Horizontal distance from observer [m]')
        plt.ylabel('Frequency [Hz]')
        plt.tight_layout()
        plt.ylim(500,10000)
        plt.yscale('log')
        plt.show()
        
        plt.figure()
        sc = plt.plot(TotalT, TotalN,color='red')
        plt.xlabel('Horizontal distance from observer [m]')
        plt.ylabel('SPL [dB]')
        plt.ylim(0,100)
        plt.tight_layout()
        plt.show()

        
    
    # the function for plotting the noise-spectrum of the flight profile 
    def plotOperation(self,S_wing,b_wing,S_tail,b_tail,theta,step):
        x=[]
        y=[]
        z=[]
        TotalT=[]
        TotalN=[]
        def FlightProfile(c1,c2,t,V1,V2,i,step):
            total=0
            fsum=0
            for f in range(400,15000,step):
                z.append(i)
                x.append(f)
                if (i<=t+50 and t<=i):
                    Result=self.SPL(f,S_wing,b_wing,S_tail,b_tail,theta,V1,c1,r)*(1-(i-t)/50)+self.SPL(f,S_wing,b_wing,S_tail,b_tail,theta,V2,c2,r)*(((i-t)/50))
                else:
                    Result=self.SPL(f,S_wing,b_wing,S_tail,b_tail,theta,V2,c2,r)
                fsum=fsum+step*10**(Result/10)
                y.append(Result.real)
            total=10*np.log10(fsum) 
            TotalN.append(total)
            TotalT.append(i)
        
        t=240
        #take-off
        for i in range(0,t,1):
            V=150/3.6+0.9*V_mach_cruise/1000*i
            r=50+asm.altitude_cruise/t*i
            total=0
            fsum=0
            for f in range(400,15000,step):
                z.append(i)
                x.append(f)
                Result=self.SPL(f,S_wing,b_wing,S_tail,b_tail,theta,V,2,r)
                y.append(Result.real)
                fsum=fsum+step*10**(Result/10)
            total=10*np.log10(fsum)    
            TotalN.append(total)
            TotalT.append(i)
            print(total.real)

       #cruise first phase 
        t=t+1
        for i in range(t,int(t+asm.time_cruise/2),10):
            r=asm.altitude_cruise
            atm =aerosandbox.Atmosphere(altitude=r)
            V=atm.speed_of_sound()*asm.mach_cruise
            FlightProfile(2,1,t,150/3.6+0.9*V_mach_cruise,V_mach_cruise,i,10)

        
        #Max cruise
        t=t+int(asm.time_cruise/2)+1
        for i in range(t,int(t+asm.time_mach_max),10):
            r=asm.altitude_mach_max
            atm = aerosandbox.Atmosphere(altitude=r)
            V=atm.speed_of_sound()*asm.mach_max
            FlightProfile(1,2,t,V_mach_cruise,V_mach_max,i,10)

        t=t+1+int(asm.time_mach_max)       
        
        #cruise second phase 
        for i in range(t,int(t+asm.time_cruise/2),10):
            r=asm.altitude_cruise
            atm = aerosandbox.Atmosphere(altitude=r)
            V=atm.speed_of_sound()*asm.mach_cruise
            FlightProfile(2,1,t,V_mach_max,V_mach_cruise,i,10)

        t=t+1+int(asm.time_cruise/2)

        #Landing approach 1
        for i in range(t,t+400,1):
            r=50+asm.altitude_cruise*(1-(i-t)/400)
            FlightProfile(1,0,t,V_mach_cruise,V_landing,i,10)
        t=t+401
        #aborted attempt
        
        for i in range(t,t+60,1):
            r=50+(i-t)*450/60
            print(r)
            FlightProfile(0,2,t,V_landing,V_goaround,i,10)
        t=t+61

        #loiter 
        for i in range(t,t+480,1):
            r=500
            FlightProfile(2,1,t,V_goaround,V_goaround,i,10)

        t=t+480
        #Final Landing approach 1
        for i in range(t,t+100,1):
            r=500-450*((i-t)/100)
            FlightProfile(1,0,t,V_goaround,V_landing,i,10)


        plt.figure()
        sc = plt.scatter(z, x, c=y, cmap='viridis', s=10,vmin=0, vmax=40)
        plt.colorbar(sc, label='SPL (in decibels)')
        plt.xlabel('Time [s]')
        plt.ylabel('Frequency [Hz]')
        plt.tight_layout()
        plt.yscale('log')
        plt.show()
        
        plt.figure()
        sc = plt.plot(TotalT, TotalN,color='blue')
        plt.xlabel('Time [s]')
        plt.ylabel('SPL [dB]')
        plt.ylim(0,100)
        plt.tight_layout()
        plt.show()
        
        return ("done")
        
       
                


def run_self_tests():
    def assert_(condition, msg):
        if not condition:
            raise AssertionError(f"FAIL: {msg}")
        print(f"  OK  {msg}")

    print("Running self-tests...")


    # Power 
    assert_(NoJet.SPL_idle(1000) < NoJet.SPL_cruise(1000) < NoJet.SPL_max(1000),
            "idle < cruise < max")

    # Physical range
    for f in range(200, 15000, 1000):
        assert_(20 < NoJet.SPL_idle(f) < 140, f"SPL_idle range at {f} Hz")
        assert_(20 < NoJet.SPL_max(f)  < 140, f"SPL_max range at {f} Hz")
        assert_(20 < NoJet.SPL_cruise(f)  < 140, f"SPL_max range at {f} Hz")

    nfw = NoFusWing(S_wing, b_wing)
    assert_(np.isfinite(nfw.SPL(1000, 0, 200,100)), "wing SPL finite")
    assert_(nfw.SPL(1000, 0, 200,100) > nfw.SPL(1000, 0, 100,100), "louder at higher speed")

    # Inverse square law: doubling r 6 dB
    n    = Noise()
    s100 = n.SPL(1000, S_wing, b_wing,S_tail,b_tail, 0, 200, 1, 100)
    s200 = n.SPL(1000, S_wing, b_wing,S_tail,b_tail, 0, 200, 1, 200)
    assert_(abs((s100 - s200) - 6.0206) < 0.05, "6 dB per doubling of distance")

    # Max louder than idle
    assert_(n.SPL(1000, S_wing, b_wing,S_tail,b_tail, 0, 200, 2, 100) >
            n.SPL(1000, S_wing, b_wing,S_tail,b_tail, 0, 200, 0, 100), "max > idle")
    # Max louder than idle
    assert_(n.SPL(1000, S_wing+10, b_wing+10,S_tail,b_tail, 0, 200, 2, 100) >
            n.SPL(1000, S_wing, b_wing,S_tail,b_tail, 0, 200, 2, 100), "louder when geometry is larger")

    print("All tests passed.")


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        run_self_tests()
    else:
        noise = Noise()
        noise.plotOperation(S_wing,b_wing,S_tail,b_tail, theta,10)
        noise.plotFlyover(S_wing,b_wing,S_tail,b_tail,0,V_mach_max,2,1000,2000,10)

