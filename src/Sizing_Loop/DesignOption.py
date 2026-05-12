import sys
import os

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