from dataclasses import dataclass

@dataclass
class EngineParameters():
    thrust_max:float
    diameter:float
    length:float


@dataclass
class PropulsionParameters():
    engine_parameters:EngineParameters
    n_engines:int = 1
    
    def thrust_max_total(self) -> float:
        return self.n_engines * self.engine_parameters.thrust_max