from dataclasses import dataclass
import numpy as np

@dataclass
class PerformanceAtAltitude:
    inviscid_ratio:float
    CD0:float

    def glide_ratio_max(self) -> float:
        return .5 * np.sqrt(self.inviscid_ratio / self.CD0)
    

    def CL_glide_ratio_max(self) -> float:
        return np.sqrt(self.inviscid_ratio * self.CD0)


@dataclass
class PerformanceParameters:
    cruise_parameters:PerformanceAtAltitude
    mach_max_parameters:PerformanceAtAltitude
    go_around_parameters:PerformanceAtAltitude
    takeoff_parameters:PerformanceAtAltitude
    climb_OEI_parameters:PerformanceAtAltitude
    
