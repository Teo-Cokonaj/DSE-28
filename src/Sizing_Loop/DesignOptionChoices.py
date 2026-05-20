from dataclasses import dataclass

@dataclass
class DesignOptionChoices:
    canard_capability:bool = False
    landing_gear_sideways_extendable:bool = False
    wing_interference_factor:float = 1.
    main_wing_x_range:float = 0.