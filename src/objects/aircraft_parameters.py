import aerosandbox.numpy as np

class AircraftParameters:
    def __init__(self,
                 total_mass: float,
                 horizontal_stabilizer_distance_from_wing: float,
                 vertical_stabilizer_distance_from_wing: float,
                 canard_distance_in_front_of_wing: float,
                 thrust_weight_ratio: float = 0.,
                 empty_mass_fraction:float = .4,
                 fuel_mass_fraction:float = .3,
                 x_cg_per_mac:float = .25,
                 z_horizontal_stabiliser:float = .5,
                 z_vertical_stabiliser_root:float = 0.,
                 z_canard:float = 0.
                 ):

        self.total_mass=total_mass
        self.horizontal_stabilizer_distance_from_wing = horizontal_stabilizer_distance_from_wing
        self.vertical_stabilizer_distance_from_wing = vertical_stabilizer_distance_from_wing
        self.canard_distance_in_front_of_wing = canard_distance_in_front_of_wing

        self.thrust_weight_ratio = thrust_weight_ratio
        self.empty_mass_fraction = empty_mass_fraction
        self.fuel_mass_fraction = fuel_mass_fraction
        self.x_cg_per_mac = x_cg_per_mac

        self.z_horizontal_stabilizer = z_horizontal_stabiliser
        self.z_vertical_stabiliser_root = z_vertical_stabiliser_root
        self.z_canard = z_canard

        def example_function(self):

            return
        