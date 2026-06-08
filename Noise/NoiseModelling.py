import numpy as np
from ConstantsForNoisemodelling import *
import matplotlib.pyplot as plt


# Data taken from article Micro Turbojet Engine Nozzle Ejector Impact on the Acoustic Emission, Thrust Force and Fuel Consumption Analysis
# Data used for the polynomic regression can be found at:     
 
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
            
        NoFusWingSPL=NoFusWing(S,b).SPL(f,theta,V)
        NoTurb=np.log10(2)+NoJetSPL
        SPL_total= np.log10((10**NoFusWingSPL+10**NoTurb))+20*np.log10(1/r) #np.log10((10**NoTurb)) #20*np.log10(1/r)10**NoFusWingSPL (10**NoFusWingSPL)
        return(SPL_total)
    def plotFlyover(self,S,b,theta,V,c,r):
        x=[]
        y=[]
        z=[]
        for i in range(0,2000,1):
            rit=r/(np.sin(np.pi/1000+i*np.pi/1.01/2000))
            for f in range(400,15000,20):
                z.append(i)
                x.append(f)
                Result=self.SPL(f,S,b,theta,V,2,rit)
                y.append(Result.real)
        plt.figure()
        sc = plt.scatter(z, x, c=y, cmap='viridis', s=40)
        plt.colorbar(sc, label='SPL (in decibels)')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.tight_layout()
        plt.show()
        return ("done")
    
    def plotOperation(self,S,b,theta,V):
        x=[]
        y=[]
        z=[]
        for i in range(0,1000,10):
            V=V+0.005*i
            for f in range(200,15000,20):
                z.append(i)
                x.append(f)
                r=i+1
                Result=self.SPL(f,S,b,theta,V,2,r)
                y.append(Result.real)
        
        for i in range(1000,2000,10):
            for f in range(200,15000,20):
                z.append(i)
                x.append(f)
                r=1000
                if (i<=1300 and 1000<=i):
                    Result=self.SPL(f,S,b,theta,V,2,r)*(1-(i-1000)/300)+self.SPL(f,S,b,theta,V,1,r)*((i-1000)/300)
                else:
                    Result=self.SPL(f,S,b,theta,V,1,r)
                #Result=self.SPL(f,S,b,theta,h,V,1,r)
                y.append(Result.real)
        
        for i in range(2000,2500,10):
            V=V-0.01*i
            for f in range(200,15000,20):
                z.append(i)
                x.append(f)
                r=1000-(i-2000)*2+0.001
                if (i<=2100 and 2000<=i):
                    Result=self.SPL(f,S,b,theta,V,1,r)*(1-(i-2000)/100)+self.SPL(f,S,b,theta,V,0,r)*((i-2000)/100)
                else:
                    Result=self.SPL(f,S,b,theta,V,0,r)
                y.append(Result.real)
        
        plt.figure()
        sc = plt.scatter(z, x, c=y, cmap='viridis', s=40)
        plt.colorbar(sc, label='SPL (in decibels)')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.tight_layout()
        plt.show()
        return ("done")
                
                
           
    
noise = Noise()
noise.plotFlyover(S,b,theta,V,2,1000)
noise.plotOperation(S,b,theta,V)







""" 
Unused code for the calculation of the noise generated by the landing gear    
class NoLandingGear():  
   def __init__(self,N_s:int, N_t:int):
        self.N_s=N_s  
        self.N_t=N_t    
    def SPL(self,f,V,Di):
        V_l=0.8*V
        S_ti=np.log(f*Di/V_l)
        DeltaSPL=X0+X1*S_ti+X2*S_ti**2+X3*S_ti**3+X4*S_ti**4+X5*S_ti**5+X6*S_ti**6+X7*S_ti**7
        SPL=Delta_i+60*np.log(V_l/c)+20*np.log(Di*np.sin(theta))+10*np.log(self.N_s*self.N_t)+DeltaSPL
        return SPL
"""