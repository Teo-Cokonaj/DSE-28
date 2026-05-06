import numpy as np

class WingPlanform:
    def __init__(self,
                 aspect_ratio: float,
                 span: float, 
                 sweep_quarter_deg: float,
                 taper: float,
                 ):

        self.aspect_ratio = aspect_ratio
        self.span = span
        self.half_span=self.span/2
        self.sweep_quarter_rad = np.radians(sweep_quarter_deg)
        self.taper = taper

        self.wing_area=self.span**2/self.aspect_ratio
        self.c_root=self.wing_area*self.half_span/((1+self.taper))
        self.c_tip=self.taper*self.c_root
        self.MAC = 2/3 * self.c_root * ((1 + self.taper + self.taper**2) / (1 + self.taper))

        def example_function(self):

            return
        