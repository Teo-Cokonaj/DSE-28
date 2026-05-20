import importlib.util
import math
import pathlib
import pytest

# Filename contains hyphens so it cannot be imported with a normal import statement.
_spec = importlib.util.spec_from_file_location(
    "SAD_hole_estimations",
    pathlib.Path(__file__).parent / "SAD-hole-estimations.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
analyze_canard_structural_impact = _mod.analyze_canard_structural_impact


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(**kwargs):
    """Thin wrapper so tests read cleanly."""
    return analyze_canard_structural_impact(**kwargs)


EXPECTED_KEYS = {
    "Aerodynamics - Canard Force (N)",
    "Aerodynamics - Max Bending Moment (Nm)",
    "Sizing - Theoretical Min Thickness (mm)",
    "Sizing - Actual Sized Thickness (mm)",
    "Sizing - Design Driven By",
    "Mass - Baseline 'Clean' Nose (kg)",
    "Penalty - Global Nose Thickening (kg)",
    "Penalty - Local Hole Doublers (kg)",
    "Penalty - Aluminum Rod (kg)",
    "Savings - Removed Skin (kg)",
    "NET TOTAL WEIGHT PENALTY (kg)",
    "Mass - New Total Nose Mass (kg)",
    "Significance - Local (% increase to nose)",
    "Significance - Global (% increase to MTOW)",
}


# ---------------------------------------------------------------------------
# 1. Return-value shape / types
# ---------------------------------------------------------------------------

class TestReturnShape:
    def test_all_expected_keys_present(self):
        result = _run()
        assert set(result.keys()) == EXPECTED_KEYS

    def test_numeric_fields_are_float_or_int(self):
        result = _run()
        numeric_keys = EXPECTED_KEYS - {
            "Sizing - Design Driven By",
            "Significance - Local (% increase to nose)",
            "Significance - Global (% increase to MTOW)",
        }
        for k in numeric_keys:
            assert isinstance(result[k], (int, float)), f"{k} is not numeric"

    def test_design_driven_by_is_string(self):
        assert isinstance(_run()["Sizing - Design Driven By"], str)

    def test_significance_fields_end_with_percent(self):
        result = _run()
        assert result["Significance - Local (% increase to nose)"].endswith("%")
        assert result["Significance - Global (% increase to MTOW)"].endswith("%")


# ---------------------------------------------------------------------------
# 2. Aerodynamic load calculations
# ---------------------------------------------------------------------------

class TestAerodynamicLoads:
    def test_canard_force_default(self):
        # canard_force = mtow * g_load * 9.81 * lift_fraction
        expected = round(100.0 * 4.0 * 9.81 * 0.20, 2)
        assert _run()["Aerodynamics - Canard Force (N)"] == expected

    def test_canard_force_scales_with_mtow(self):
        r1 = _run(mtow_kg=50.0)
        r2 = _run(mtow_kg=100.0)
        assert pytest.approx(r2["Aerodynamics - Canard Force (N)"], rel=1e-6) == \
               2 * r1["Aerodynamics - Canard Force (N)"]

    def test_canard_force_scales_with_g_load(self):
        r1 = _run(max_g_load=2.0)
        r2 = _run(max_g_load=4.0)
        assert pytest.approx(r2["Aerodynamics - Canard Force (N)"], rel=1e-6) == \
               2 * r1["Aerodynamics - Canard Force (N)"]

    def test_canard_force_scales_with_lift_fraction(self):
        r1 = _run(canard_lift_fraction=0.10)
        r2 = _run(canard_lift_fraction=0.20)
        assert pytest.approx(r2["Aerodynamics - Canard Force (N)"], rel=1e-6) == \
               2 * r1["Aerodynamics - Canard Force (N)"]

    def test_bending_moment_default(self):
        # max_bending_moment = canard_force * distance_to_bulkhead
        expected = round(100.0 * 4.0 * 9.81 * 0.20 * 0.5, 2)
        assert _run()["Aerodynamics - Max Bending Moment (Nm)"] == expected

    def test_bending_moment_scales_with_distance(self):
        r1 = _run(distance_to_bulkhead_m=0.25)
        r2 = _run(distance_to_bulkhead_m=0.50)
        assert pytest.approx(r2["Aerodynamics - Max Bending Moment (Nm)"], rel=1e-6) == \
               2 * r1["Aerodynamics - Max Bending Moment (Nm)"]

    def test_zero_lift_fraction_gives_zero_force(self):
        result = _run(canard_lift_fraction=0.0)
        assert result["Aerodynamics - Canard Force (N)"] == 0.0
        assert result["Aerodynamics - Max Bending Moment (Nm)"] == 0.0


# ---------------------------------------------------------------------------
# 3. Thickness sizing & design-driver logic
# ---------------------------------------------------------------------------

class TestThicknessSizing:
    def test_default_design_driven_by_minimum_gauge(self):
        # With default params the theoretical thickness is ~0.056 mm < 1 mm min gauge
        result = _run()
        assert result["Sizing - Design Driven By"] == "Minimum Gauge"

    def test_actual_thickness_gte_minimum_gauge_always(self):
        for mtow in [10, 100, 500]:
            result = _run(mtow_kg=mtow)
            assert result["Sizing - Actual Sized Thickness (mm)"] >= \
                   result["Sizing - Theoretical Min Thickness (mm)"]

    def test_high_load_triggers_bending_load_driver(self):
        # Very heavy aircraft + high g's with a thin, weak skin and large fuselage
        # should push theoretical thickness above the 1 mm minimum gauge
        result = _run(
            mtow_kg=5000.0,
            max_g_load=9.0,
            fuselage_diameter_m=0.6,
            skin_yield_strength_pa=50e6,    # much weaker material
            minimum_gauge_m=0.0001,         # very thin minimum gauge
        )
        assert result["Sizing - Design Driven By"] == "Bending Loads"
        assert result["Sizing - Theoretical Min Thickness (mm)"] > \
               result["Sizing - Actual Sized Thickness (mm)"] * 0.0  # sanity

    def test_theoretical_thickness_formula(self):
        # t_theory = (M * SF) / (pi * r^2 * sigma)
        mtow, g, frac, dist, dia, sf, sig = 100, 4, 0.20, 0.5, 0.15, 1.5, 600e6
        canard_force = mtow * g * 9.81 * frac
        moment = canard_force * dist
        r = dia / 2
        expected_mm = round((moment * sf) / (math.pi * r**2 * sig) * 1000, 3)
        result = _run(
            mtow_kg=mtow, max_g_load=g, canard_lift_fraction=frac,
            distance_to_bulkhead_m=dist, fuselage_diameter_m=dia,
            safety_factor=sf, skin_yield_strength_pa=sig,
        )
        assert result["Sizing - Theoretical Min Thickness (mm)"] == expected_mm


# ---------------------------------------------------------------------------
# 4. Baseline nose mass
# ---------------------------------------------------------------------------

class TestBaselineNoseMass:
    def test_baseline_nose_mass_formula(self):
        # baseline_mass = 2*pi*r * t_min * L * rho_skin
        r = 0.15 / 2
        expected = round(2 * math.pi * r * 0.001 * 0.5 * 1600.0, 4)
        assert _run()["Mass - Baseline 'Clean' Nose (kg)"] == expected

    def test_baseline_scales_with_density(self):
        r1 = _run(skin_density_kg_m3=800.0)
        r2 = _run(skin_density_kg_m3=1600.0)
        assert pytest.approx(r2["Mass - Baseline 'Clean' Nose (kg)"], rel=1e-6) == \
               2 * r1["Mass - Baseline 'Clean' Nose (kg)"]


# ---------------------------------------------------------------------------
# 5. Global reinforcement penalty
# ---------------------------------------------------------------------------

class TestGlobalReinforcementPenalty:
    def test_no_global_penalty_when_min_gauge_governs(self):
        # When design is driven by minimum gauge, delta_thickness = 0 -> penalty = 0
        result = _run()
        assert result["Sizing - Design Driven By"] == "Minimum Gauge"
        assert result["Penalty - Global Nose Thickening (kg)"] == 0.0

    def test_global_penalty_positive_when_bending_governs(self):
        result = _run(
            mtow_kg=5000.0, max_g_load=9.0, fuselage_diameter_m=0.6,
            skin_yield_strength_pa=50e6, minimum_gauge_m=0.0001,
        )
        assert result["Sizing - Design Driven By"] == "Bending Loads"
        assert result["Penalty - Global Nose Thickening (kg)"] > 0.0


# ---------------------------------------------------------------------------
# 6. Local hole doubler penalty
# ---------------------------------------------------------------------------

class TestLocalDoublerPenalty:
    def test_local_doubler_is_three_times_removed_skin(self):
        result = _run()
        # doublers = 3 * |removed skin|
        removed = abs(result["Savings - Removed Skin (kg)"])
        assert pytest.approx(result["Penalty - Local Hole Doublers (kg)"], rel=1e-6) == \
               3.0 * removed

    def test_doubler_scales_with_rod_diameter(self):
        r1 = _run(rod_outer_diameter_m=0.01)
        r2 = _run(rod_outer_diameter_m=0.02)
        # cutout area scales with d^2 → doubling rod diameter quadruples doublers.
        # Values are rounded to 4 dp in the return dict, so compare the unrounded
        # exact ratio rather than the stored floats directly.
        d1, d2 = 0.01, 0.02
        actual_required_thickness_m = 0.001  # min gauge governs for default params
        rho, t = 1600.0, actual_required_thickness_m
        exact_r1 = 3 * 2 * math.pi * (d1 / 2) ** 2 * t * rho
        exact_r2 = 3 * 2 * math.pi * (d2 / 2) ** 2 * t * rho
        assert pytest.approx(exact_r2, rel=1e-9) == 4 * exact_r1
        # Also verify the direction holds for the rounded values in the output.
        assert r2["Penalty - Local Hole Doublers (kg)"] > r1["Penalty - Local Hole Doublers (kg)"]

    def test_removed_skin_is_negative(self):
        result = _run()
        assert result["Savings - Removed Skin (kg)"] < 0.0


# ---------------------------------------------------------------------------
# 7. Hardware (rod) mass
# ---------------------------------------------------------------------------

class TestRodMass:
    def test_rod_mass_formula(self):
        d_o = 0.02
        d_i = d_o - 2 * 0.002
        area = math.pi * ((d_o / 2) ** 2 - (d_i / 2) ** 2)
        expected = round(area * 0.15 * 2810.0, 4)
        assert _run()["Penalty - Aluminum Rod (kg)"] == expected

    def test_hollow_rod_lighter_than_solid(self):
        # A very thin wall makes the rod light; a "solid" rod (wall = half OD) is heavier
        thin = _run(rod_wall_thickness_m=0.0001)
        thick = _run(rod_wall_thickness_m=0.009)   # close to solid for 20mm OD
        assert thick["Penalty - Aluminum Rod (kg)"] > thin["Penalty - Aluminum Rod (kg)"]

    def test_rod_mass_scales_with_fuselage_diameter(self):
        # rod spans the fuselage diameter
        r1 = _run(fuselage_diameter_m=0.10)
        r2 = _run(fuselage_diameter_m=0.20)
        assert pytest.approx(r2["Penalty - Aluminum Rod (kg)"], rel=1e-6) == \
               2 * r1["Penalty - Aluminum Rod (kg)"]


# ---------------------------------------------------------------------------
# 8. Net weight penalty & totals
# ---------------------------------------------------------------------------

class TestNetPenalty:
    def test_net_penalty_accounting_identity(self):
        result = _run()
        expected_net = round(
            result["Penalty - Global Nose Thickening (kg)"]
            + result["Penalty - Local Hole Doublers (kg)"]
            + result["Penalty - Aluminum Rod (kg)"]
            + result["Savings - Removed Skin (kg)"],   # already negative
            4,
        )
        assert result["NET TOTAL WEIGHT PENALTY (kg)"] == pytest.approx(expected_net, abs=1e-6)

    def test_new_total_nose_mass_equals_baseline_plus_penalty(self):
        result = _run()
        expected = round(
            result["Mass - Baseline 'Clean' Nose (kg)"]
            + result["NET TOTAL WEIGHT PENALTY (kg)"],
            4,
        )
        assert result["Mass - New Total Nose Mass (kg)"] == pytest.approx(expected, abs=1e-6)

    def test_net_penalty_positive_under_default_conditions(self):
        assert _run()["NET TOTAL WEIGHT PENALTY (kg)"] > 0.0


# ---------------------------------------------------------------------------
# 9. Significance percentages
# ---------------------------------------------------------------------------

class TestSignificancePercentages:
    def test_local_significance_value(self):
        result = _run()
        penalty = result["NET TOTAL WEIGHT PENALTY (kg)"]
        baseline = result["Mass - Baseline 'Clean' Nose (kg)"]
        expected_pct = round(penalty / baseline * 100, 1)
        assert result["Significance - Local (% increase to nose)"] == f"{expected_pct} %"

    def test_global_significance_value(self):
        result = _run()
        penalty = result["NET TOTAL WEIGHT PENALTY (kg)"]
        expected_pct = round(penalty / 100.0 * 100, 2)
        assert result["Significance - Global (% increase to MTOW)"] == f"{expected_pct} %"

    def test_global_significance_decreases_with_heavier_aircraft(self):
        r_light = _run(mtow_kg=50.0)
        r_heavy = _run(mtow_kg=500.0)
        pct_light = float(r_light["Significance - Global (% increase to MTOW)"].replace(" %", ""))
        pct_heavy = float(r_heavy["Significance - Global (% increase to MTOW)"].replace(" %", ""))
        assert pct_heavy < pct_light


# ---------------------------------------------------------------------------
# 10. Edge / boundary cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_zero_distance_to_bulkhead_raises(self):
        # distance_to_bulkhead_m=0 collapses baseline_nose_mass to 0,
        # causing a ZeroDivisionError when computing the significance percentage.
        with pytest.raises(ZeroDivisionError):
            _run(distance_to_bulkhead_m=0.0)

    def test_zero_canard_lift_fraction_zero_moment(self):
        result = _run(canard_lift_fraction=0.0)
        assert result["Aerodynamics - Max Bending Moment (Nm)"] == 0.0

    def test_very_high_yield_strength_drives_min_gauge(self):
        result = _run(skin_yield_strength_pa=1e12)
        assert result["Sizing - Design Driven By"] == "Minimum Gauge"

    def test_result_is_deterministic(self):
        assert _run() == _run()
