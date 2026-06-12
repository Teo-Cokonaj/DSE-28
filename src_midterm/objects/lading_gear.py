from dataclasses import dataclass

@dataclass
class LandingGear():
    x_main_lg:float
    x_nose_lg:float
    length_z:float
    y_main_lg:float

    def length_pythagorean(self):
        return (self.length_z**2 + self.y_main_lg**2)**.5
