import sys
import os
import typing as ty
import numpy.typing as nt
import aerosandbox.numpy as np

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Sizing_Loop.DesignOptionState import DesignOptionState
from src.Sizing_Loop.DesignOptionStep import DesignOptionStep

class DesignOption:
    def __init__(self, state:DesignOptionState, steps:list[DesignOptionStep]):
        self.state = state
        self.steps = steps


    def iteration_step(self):
        for step in self.steps:
            self.state.iterable = step.update(self.state)


    def iterate_for_n_steps(self, n:int, convergence_criterion:ty.Callable[[DesignOptionState], nt.NDArray[np.float_]]) -> list[float]:
        convergence_quantities_initial = convergence_criterion(self.state)
        assert convergence_quantities_initial.ndim == 1

        convergence_quantities = np.zeros((len(convergence_quantities_initial), n+1))
        convergence_quantities[:, 0] = convergence_quantities_initial

        for iteration_number in range(1, n+1):
            self.iteration_step()
            convergence_quantities[:, iteration_number] = convergence_criterion(self.state)

        return convergence_quantities