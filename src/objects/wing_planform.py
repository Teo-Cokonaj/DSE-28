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
        self.sweep_quarter_rad = np.radians(sweep_quarter_deg)
        self.taper = taper

        self.wing_area=self.span**2/self.aspect_ratio

        def example_function(self):

            return
        