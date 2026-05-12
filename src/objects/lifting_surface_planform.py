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
        self.tip_twist = tip_twist_rad
        self.sweep_quarter_rad = np.radians(sweep_quarter_deg)
        self.taper = taper
        self.wing_area = span**2/aspect_ratio

        self.chords = None #add chord calculation here!
        self.LE_positions = None #add LE position calculator here!


    @property
    def span(self)->float:
        return np.sqrt(self.wing_area * self.aspect_ratio)
    

    @property
    def half_span(self)->float:
        return self.span/2
    

    @property
    def c_root(self)->float:
       return 2*self.wing_area/(self.span*(1+self.taper)) 
        

    @property
    def c_tip(self)->float:
        return self.taper*self.c_root
    

    @property
    def sweep_LE_rad(self)->float:
        return np.arctan(np.tan(self.sweep_quarter_rad) + self.c_root / self.span / 2 * (1 - self.taper))
    

    @property
    def MAC(self)->float:
        return 2/3 * self.c_root * ((1 + self.taper + self.taper**2) / (1 + self.taper))
    

    @property
    def y_MAC(self)->float:
        return self.half_span/3*((1+2*self.taper)/(1+self.taper))
    

    @property
    def x_MAC(self)->float:
        return self.y_MAC*np.tan(self.sweep_LE_rad)