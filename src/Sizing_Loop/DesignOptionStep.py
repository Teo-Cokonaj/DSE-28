import abc

import sys
import os

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Sizing_Loop.DesignOptionState import DesignOptionState
from src.Sizing_Loop.DesignOptionStateIterable import DesignOptionStateIterable

class DesignOptionStep(abc.ABC):

    @abc.abstractmethod
    def update(self, state:DesignOptionState) -> DesignOptionStateIterable:
        '''
        conducts a sizing step - based on an aircraft state (the input) performs a calculation based on 
        which a (partially) updated set of design variables is returned
        '''
        raise NotImplementedError()