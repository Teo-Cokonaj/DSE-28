import pytest
import sys
import os
import numpy.testing as nte
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src_final.Requirements.MassReq import MassReq
from src_final.Aircraft.Aircraft import Aircraft
from src_final.Aircraft.Planform import Planform
from src_final.Aircraft.Fixed import Fixed

# Define an MTOW constraint
@pytest.fixture
def mtow_max():
    mtow_max = 100      # [kg]
    return mtow_max

@pytest.fixture
def aircraft_mass():
    aircraft = Aircraft(fixed = Fixed, planforms = list[Planform])
    return aircraft.total_mass()

class TestMassReq:
    def test_MassReq(self, 
                    aircraft_mass,
                    mtow_max):
        print(f'MTOW HUGO requirement: {mtow_max}')
        print(f'Total HUGO mass: {aircraft_mass}')
        print(f'Total MTOW margin: {mtow_max-aircraft_mass}')
        assert(mtow_max>=aircraft_mass)