import pytest as pt
import aerosandbox.numpy as np
import sys
import os
import matplotlib.pyplot as plt
import pytest
import aerosandbox as asb

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.MatchingDiagram.MatchingDiagram import MatchingDiagram
from src.MatchingDiagram.MatchingDiagramJet import MatchingDiagramJet

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
        matching_diagram.create_wing_loading_axis()

        penalty = lambda wing_loading, thrust_weight: thrust_weight
        assert np.allclose(list(matching_diagram.select_design_point(penalty)), [3000., .5], rtol=1/matching_diagram.resolution), list(matching_diagram.select_design_point(penalty))

        penalty = lambda wing_loading, thrust_weight: -wing_loading #NOTE: yes 'tis correct penalty to maximise wing_loading
        assert np.allclose(list(matching_diagram.select_design_point(penalty)), [4000., 2/3], rtol=1/matching_diagram.resolution), list(matching_diagram.select_design_point(penalty))
        
        if plot:
            fig = matching_diagram.plot(*matching_diagram.select_design_point(penalty), 'lower left', 1.)
            plt.show()

    def test_jet_matching_diagram_from_textbook(self, plot=False):
        #study case from Introduction to Airplane Design by R. Vos (2023)
        #in our case without the rate of climb, as HUGO has no rate of climb requirement
        matching_diagram = MatchingDiagramJet(2, 10.)

        matching_diagram.add_approach_speed("Approach speed", 68*1.3/1.23, 2.5, beta=.85)
        assert np.isclose(matching_diagram.constraints_wing_loading["Approach speed"], 5500, atol=10.)

        matching_diagram.add_landing_field_length("Landing length", 1600.*.6/.45, 2.5, beta=.85)
        assert np.isclose(matching_diagram.constraints_wing_loading["Landing length"], 6400, atol=10.)

        matching_diagram.create_wing_loading_axis()

        matching_diagram.add_cruise_speed("Cruise speed", .8, .018, .8*8*np.pi, asb.Atmosphere(11000), .95)
        assert np.isclose(matching_diagram.constraints_thrust_weight["Cruise speed"](7000.), .29, atol=5e-3)

        matching_diagram.add_climb_gradient("Climb gradient", .02407, .038, 8*.87*np.pi, False)
        assert np.isclose(matching_diagram.constraints_thrust_weight["Climb gradient"](1000.), .26, atol=5e-3)

        matching_diagram.add_takeoff_field_length("Takeoff length", 2500., np.pi*.87*8, 1.6, asb.Atmosphere(1600., temperature_deviation=15))
        assert np.isclose(matching_diagram.constraints_thrust_weight["Takeoff length"](5000.), .32, atol=1e-2) #NOTE: looser tolerance for couldn't match the hand calculated atmospheric density with enough accuracy

        wing_loading, thrust_weight = matching_diagram.select_design_point(lambda wing_loading, thrust_weight: thrust_weight)
        #NOTE: tolerances dictated by the resolution of Figure 7.23 in the book
        assert np.isclose(wing_loading, 4400, atol=100.)
        assert np.isclose(thrust_weight, .31, atol=5e-3)

        if plot:
            fig = matching_diagram.plot(wing_loading, thrust_weight)
            plt.show()


if __name__ == "__main__":
    tester = TestMatchingDiagram()
    #tester.test_nonphysical_matching_diagram(True)
    tester.test_jet_matching_diagram_from_textbook(True)