

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Aircraft.Aircraft import Aircraft

class Requirement:

    def assess(self, aircraft:Aircraft) -> bool:
        raise NotImplementedError