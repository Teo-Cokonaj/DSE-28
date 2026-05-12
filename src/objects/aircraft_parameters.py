import aerosandbox.numpy as np

class AircraftParameters:
    def __init__(self,
                 total_mass: float,
                 horizontal_stabilizer_distance_from_wing: float,
                 vertical_stabilizer_distance_from_wing: float,
                 canard_distance_in_front_of_wing: float,
                 thrust_weight_ratio: float = 0.,
                 empty_mass_fraction:float = .4,
                 x_cg_per_mac:float = .25,
                 ):

        self.total_mass=total_mass
        self.horizontal_stabilizer_distance_from_wing = horizontal_stabilizer_distance_from_wing
        self.vertical_stabilizer_distance_from_wing = vertical_stabilizer_distance_from_wing
        self.canard_distance_in_front_of_wing = canard_distance_in_front_of_wing

        self.thrust_weight_ratio = thrust_weight_ratio
        self.empty_mass_fraction = empty_mass_fraction
        self.x_cg_per_mac = x_cg_per_mac

        def example_function(self):

            return
        