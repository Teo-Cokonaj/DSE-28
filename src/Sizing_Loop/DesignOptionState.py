from dataclasses import dataclass

import sys
import os

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Sizing_Loop.DesignOptionStateFixed import DesignOptionStateFixed
from src.Sizing_Loop.DesignOptionStateIterable import DesignOptionStateIterable

@dataclass
class DesignOptionState:
    iterable = DesignOptionStateIterable
    _fixed = DesignOptionStateFixed()

    @property
    def fixture(self) -> DesignOptionStateFixed:
        return self._fixed