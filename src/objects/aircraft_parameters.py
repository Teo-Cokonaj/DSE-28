import aerosandbox.numpy as np

class AircraftParameters:
    def __init__(self,
                 total_mass: float,
                 horizontal_stabilizer_distance_from_wing: float,
                 vertical_stabilizer_distance_from_wing: float,
                 canard_distance_in_front_of_wing: float,
                 ):

        self.total_mass=total_mass
        self.horizontal_stabilizer_distance_from_wing = horizontal_stabilizer_distance_from_wing
        self.vertical_stabilizer_distance_from_wing = vertical_stabilizer_distance_from_wing
        self.canard_distance_in_front_of_wing = canard_distance_in_front_of_wing

        def example_function(self):

            return
        