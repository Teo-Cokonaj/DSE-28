class Fueltank():
    def __init__(self, mass:float,placement:float):
        self.mass=mass          #in kg
        self.placement=placement     #in meters measured from tip of aircraft
    def print(self):
        return(print(self.mass,self.placement))
    def force(self):
        force=self.mass*g
        return(force)
    
class Aircraft(): 
    def __init__(self, cg: float, empty_mass:float ):
        self.cg=cg
        self.empty_mass=empty_mass
    def cg_calc(self,F1,F2):
        cg_new=self.cg+((F1.placement-self.cg)*F1.mass+(F2.placement-self.cg)*F2.mass)/(self.empty_mass+F1.mass+F2.mass)
        return (cg_new)





def run_self_tests():
    def assert_(condition, msg):
        if not condition:
            raise AssertionError(f"FAIL: {msg}")
        print(f"  OK  {msg}")
    
    g = 9.81  
    def test_fueltank_stores_attributes():
        t = Fueltank(mass=100, placement=500)
        assert t.mass == 100
        assert t.placement == 500

    def test_cg_unchanged_when_both_tanks_empty():
        a = Aircraft(cg=1000, empty_mass=100)
        F1 = Fueltank(mass=0, placement=800)
        F2 = Fueltank(mass=0, placement=1200)
        assert a.cg_calc(F1, F2) == 1000

    def test_cg_shifts_forward_with_nose_weight():
        a = Aircraft(cg=1000, empty_mass=100)
        F1 = Fueltank(mass=50, placement=500)   # ahead of CG
        F2 = Fueltank(mass=0,  placement=1500)
        result = a.cg_calc(F1, F2)
        assert result < 1000

    def test_cg_shifts_aft_with_tail_weight():
        a = Aircraft(cg=1000, empty_mass=100)
        F1 = Fueltank(mass=0,  placement=500)
        F2 = Fueltank(mass=50, placement=1500)  # behind CG
        result = a.cg_calc(F1, F2)
        assert result > 1000

    def test_cg_symmetric_tanks_no_shift():
        a = Aircraft(cg=1000, empty_mass=100)
        F1 = Fueltank(mass=25, placement=800)
        F2 = Fueltank(mass=25, placement=1200)
        result = a.cg_calc(F1, F2)
        assert abs(result - 1000) < 1e-9

    def test_cg_tank_at_cg_no_shift():
        a = Aircraft(cg=1000, empty_mass=100)
        F1 = Fueltank(mass=50, placement=1000)  # right at CG
        F2 = Fueltank(mass=0,  placement=500)
        result = a.cg_calc(F1, F2)
        assert abs(result - 1000) < 1e-9


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        run_self_tests()
    else: 
        F1=Fueltank(mass=0,placement=1142.5)
        F2=Fueltank(mass=8/2,placement=1492.5)
        A1=Aircraft(1414,42.2-13.54)
        print(A1.cg_calc(F1,F2))


        F1=Fueltank(mass=8/2,placement=1142.5)
        F2=Fueltank(mass=0,placement=1492.5)
        A1=Aircraft(1414,46.76-13.54)
        print(A1.cg_calc(F1,F2))





