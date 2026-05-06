import sys
import os
import numpy as np
from dataclasses import dataclass

@dataclass
class Class_I_Result:
    mtom: float
    fuel_fraction: float
    oem_fraction: float

    @property
    def fuel_mass(self) -> float:
        return self.mtom*self.fuel_fraction
    
    @property
    def oem_mass(self) -> float:
        return self.mtom*self.oem_fraction
    
    @property
    def payload_fraction(self) -> float:
        return 1-self.fuel_fraction-self.oem_fraction