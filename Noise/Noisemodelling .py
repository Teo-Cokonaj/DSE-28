import numpy as np
from ConstansForNoisemodelling import *

delta=1.51*10**(−5)
V=100
h=100
theta=0
phi=0

class Noise(): 
    def __init__(self,):
        self.Jet=NoJet()
        self.FusWing=NoFusWing()
        self.LandingGear=NoLandingGear()
        
           
class NoJet():
    def __init__(self):
    def SPL(f):  
        SPL=3.7747e-30*f**10 - 6.0646e-26*f**9 + 4.2035e-22*f**8 - 1.6417e-18*f**7 + 3.9580e-15*f**6 - 6.0646e-12*f**5 + 5.8572e-9*f**4 - 3.4093e-6*f**3 + 0.0010748*f**2 - 0.13521*f + 84.987
        return SPL

class NoFusWing():   
    def __init__(self, S:float, b:float):
        self.WingSurface=S  
        self.span=b         
    def SPL(self,f,theta,h,V):
        delta=0.37*(self.WingSurface/self.span)*(V*self.WingSurface/self.span*nu)**(0.3)
        OASPL=50*np.log(V/51.44)+10*np.log(delta*b/(h**2)*(cos(phi)**2)*(cos(theta/2)**2))+101.3
        DeltaSPL=-0.03*(1/152.4)*(f/(0.1*V/delta)-1)**(3/2)
        SPL=OASPL+10*np.log(0.613*(f/(0.1*V/delta))**4*((f/(0.1*V/delta))**(3/2)+0.5)**(-4)+DeltaSPL+6
        return SPL
        
class NoLandingGear():
    def __init__(self,Di:float,N_s:int, N_t:int):
        
    def OASPL(f):
        V_l=0.8*V
        S_ti=np.log(f*Di/V_l)
        DeltaSPL=X0+X1*S_ti+X2*S_ti**2+X3*S_ti**3+X4*S_ti**4+X5*S_ti**5+X6*S_ti**6+X7*S_ti**7
        OASPL=Delta_i+60*np.log(V_l/c)+20*np.log(D_i*np.sin(theta))+10*np.log(N_s*N_t)+DeltaSPL
        return OASPL
        
    