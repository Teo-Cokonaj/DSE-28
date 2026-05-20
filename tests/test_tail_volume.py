import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.objects.lifting_surface_planform import LiftingSurfacePlanform
from src.tail_sizing.tail_sizing import TailVolume


@pytest.fixture
def wing_planform():
    return LiftingSurfacePlanform(aspect_ratio=25.0,
                                span=2.0,
                                sweep_quarter_deg=30.0,
                                taper=1.0,
                                tip_twist_rad=0.0)

@pytest.fixture
def tail_volume(wing_planform,
                ):
    return TailVolume(wing_planform=wing_planform,
                      required_cg_excursion_MAC=0.5,
                      ac_position_mac=1.0,
                      Cmac=-1.0,
                      C_L_H=2.0,
                      C_L_A_minus_H=3.0,
                      C_L_alpha_H=4.0,
                      wing_downwash_gradient=0.0,
                      C_L_alpha_A_minus_H=5.0,
                      V_H_over_V_2=1.0,
                      )


class TestTailVolume:
    def test_required_tail_volume(self,
                                  tail_volume,
                                  wing_planform,
                          ):
        tail_volume.find_required_tail_volume()
        numerator=(0.5+1.0/3.0)*wing_planform.wing_area*wing_planform.MAC
        denominator=(4.0/5.0*(1.0-0.0)-2.0/3.0)*1.0**2
        reference_tail_volume=numerator/denominator

        assert abs(reference_tail_volume-tail_volume.required_tail_volume)/reference_tail_volume <0.01

    def test_required_cg_position_MAC(self,
                                      tail_volume,
                                      wing_planform):
        tail_volume.find_required_tail_volume()
        tail_volume.find_required_cg_position_MAC()
        reference_required_cg_position_MAC=1.0+4.0/5.0*(1.0-0.0)*tail_volume.required_tail_volume/wing_planform.wing_area/wing_planform.MAC*1.0**2

        assert abs(reference_required_cg_position_MAC-tail_volume.required_CG_position_MAC)/reference_required_cg_position_MAC <0.01


