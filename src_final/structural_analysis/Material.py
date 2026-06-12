class Material:
    def __init__(self,
                 density: float,
                 elastic_modulus: float,
                 shear_modulus: float,
                 poisson_ratio: float,
                 yield_strength: float,
                 fracture_strength: float,
                 ):
        self.density=density
        self.elastic_modulus=elastic_modulus
        self.shear_modulus=shear_modulus
        self.poisson_ratio=poisson_ratio
        self.yield_strength=yield_strength
        self.fracture_strength=fracture_strength

    def example(self):
        #TODO: extract data from file
        pass
