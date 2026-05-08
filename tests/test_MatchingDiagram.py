import pytest as pt
import aerosandbox.numpy as np
import sys
import os
import matplotlib.pyplot as plt
import pytest

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.MatchingDiagram.MatchingDiagram import MatchingDiagram

@pytest.fixture
def constraints_thrust_nonphysical():
    return 


@pytest.fixture
def constraints_wing_loading_nonphysical():
    return 


class TestMatchingDiagram():
    def test_nonphysical_matching_diagram(self, plot=False):

        constraints_thrust_nonphysical = {
            'label1': lambda wing_loading: wing_loading/6000.,
            'label2': lambda wing_loading: 1-wing_loading/6000.
        }

        constraints_wing_loading_nonphysical = {
            'label3': 4000., 
            'label4': 5000., 
            'label5': 6000.
        }
        
        #just to see the mechanics of finding optima etc.
        matching_diagram = MatchingDiagram(constraints_thrust_nonphysical, constraints_wing_loading_nonphysical)

        penalty = lambda wing_loading, thrust_weight: thrust_weight
        assert np.allclose(list(matching_diagram.select_design_point(penalty)), [3000., .5], rtol=1/matching_diagram.resolution), list(matching_diagram.select_design_point(penalty))

        penalty = lambda wing_loading, thrust_weight: -wing_loading #NOTE: yes 'tis correct penalty to maximise wing_loading
        assert np.allclose(list(matching_diagram.select_design_point(penalty)), [4000., 2/3], rtol=1/matching_diagram.resolution), list(matching_diagram.select_design_point(penalty))
        
        if plot:
            fig = matching_diagram.plot(*matching_diagram.select_design_point(penalty), 'upper center')
            plt.show()


if __name__ == "__main__":
    tester = TestMatchingDiagram()
    tester.test_nonphysical_matching_diagram(True)