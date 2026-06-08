

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
        return (mass,GWP)
        