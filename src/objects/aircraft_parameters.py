import numpy as np

class AircraftParameters:
    def __init__(self,
                 total_mass: float,
                 fuselage_length: float,
                 E: float=73.1e9,
                 G: float=28.0e9,
                 rho_structural: float=2780.0
                 ):

        self.total_mass=total_mass
        self.fuselage_length = fuselage_length
        self.E=E
        self.G=G
        self.rho_structural=rho_structural

        def example_function(self):

            return
        