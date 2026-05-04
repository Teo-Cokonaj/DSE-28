import sys
import os
import numpy as np

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from global_parameters import CONSTANTS


class Mission_Segment():
    def __init__(self):
        self.glide_ratio = glide_ratio
        self.