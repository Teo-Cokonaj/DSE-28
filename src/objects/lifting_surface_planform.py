import aerosandbox.numpy as np

class LiftingSurfacePlanform:
    def __init__(self,
                 aspect_ratio: float,
                 span: float, 
                 sweep_quarter_deg: float,
                 taper: float,
                 tip_twist_rad: float,
                 ):

        self.aspect_ratio = aspect_ratio
        self.span = span
        self.tip_twist = tip_twist_rad
        self.half_span=self.span/2
        self.sweep_quarter_rad = np.radians(sweep_quarter_deg)
        self.taper = taper
        self.wing_area=self.span**2/self.aspect_ratio
        self.c_root=2*self.wing_area/(self.span*(1+self.taper))
        self.c_tip=self.taper*self.c_root
        self.sweep_LE_rad = np.arctan(np.tan(self.sweep_quarter_rad) + self.c_root / self.span / 2 * (1 - self.taper))
        self.MAC = 2/3 * self.c_root * ((1 + self.taper + self.taper**2) / (1 + self.taper))

        self.chords = None #add chord calculation here!
        self.LE_positions = None #add LE position calculator here!

        def example_function(self):

            return
        