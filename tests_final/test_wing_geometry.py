import os
import sys

import numpy as np
import pytest
from scipy.integrate import cumulative_trapezoid
from scipy.interpolate import interp1d

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import src_final.structural_analysis.wing_loading as wing_loading_module
from src_final.Aircraft.Planform import Planform
from src_final.structural_analysis.Material import Material
from src_final.structural_analysis.wing_loading import WingModel


@pytest.fixture
def material():
    return Material(
        density=1600.0,
        elastic_modulus=70e9,
        shear_modulus=5e9,
        poisson_ratio=0.3,
        yield_strength=600e6,
        fracture_strength=600e6,
    )


@pytest.fixture
def planform():
    return Planform(
        aspect_ratio=10.0,
        span=10.0,
        sweep_quarter_deg=0.0,
        taper=1.0,
        thickness_to_chord=0.12,
        cm_quarter_chord=1.0,
        wetted_surface_ratio=1.0,
        interference_factor=1.0,
        clmax=1.5,
        flap=False,
    )


@pytest.fixture
def wing_model(material, planform):
    model = WingModel(
        wing_skin_thickness_m=0.01,
        number_of_nodes=4,
        material_1=material,
        planform=planform,
        load_factor=1,
        load_factor_maneuver=1,
        local_fuselage_diameter=0.31

    )

    chord_stations, _, y_stations, dy = planform.sectional_properties(
        number_of_sections=model.number_of_nodes
    )
    model.chord_stations = np.asarray(chord_stations, dtype=float)
    model.y_stations_chord = np.asarray(y_stations, dtype=float)
    model.y_stations = model.y_stations_chord
    model.dy = np.asarray(dy, dtype=float)
    model.span_poz = model.y_stations_chord[1:]
    model.lift_span = np.array([30.0, 20.0, 10.0])
    model.force_distribution = np.array([8.0, 12.0, 16.0])

    # Some WingModel methods currently read these names as module globals.
    wing_loading_module.planform = planform
    wing_loading_module.material_1 = material

    return model


class TestWingModel:
    def test_planform_data_sets_span_lift_chord_and_station_arrays(self, wing_model):
        span_poz, lift_span, chords, y_stations, dy = wing_model.planform_data()

        assert span_poz.ndim == 1
        assert span_poz.shape == lift_span.shape
        assert chords.shape == y_stations.shape == (wing_model.number_of_nodes,)
        assert dy.shape == (wing_model.number_of_nodes - 1,)
        assert np.all(np.isfinite(lift_span))
        assert np.all(np.isfinite(span_poz))
        np.testing.assert_allclose(wing_model.y_stations, y_stations)



    def test_perimeter_and_area(self, wing_model):
        perimeter, area = wing_model.perimeter_area_of_section()

        a = wing_model.chord_stations
        b = a * wing_model.planform.thickness_to_chord
        h = (a - b) ** 2 / (a + b) ** 2
        expected_perimeter = np.pi * (a + b) * (
            1 + (3 * h) / (10 + np.sqrt(4 - 3 * h))
        )
        t = wing_model.wing_skin_thickness_m
        expected_area = np.pi * (a * b - (a - 2 * t) * (b - 2 * t)) / 4

        np.testing.assert_allclose(perimeter, expected_perimeter)
        np.testing.assert_allclose(area, expected_area)



    def test_area_moment_inertia(self, wing_model):
        ix, iy = wing_model.area_moment_inertia()

        a = wing_model.chord_stations
        b = a * wing_model.planform.thickness_to_chord
        t = wing_model.wing_skin_thickness_m
        ix_expected = np.pi * (a * b**3 - ((a - 2 * t) * (b - 2 * t)**3)) / 64
        iy_expected = np.pi * b * a**3 / 4

        np.testing.assert_allclose(ix, ix_expected)
        np.testing.assert_allclose(iy, iy_expected)



    def test_force_per_unit_subtracts_skin_weight_from_lift(self, wing_model, material):
        force, lift, weight = wing_model.force_per_unit(plot=False)

        perimeter, _ = wing_model.perimeter_area_of_section()
        expected_weight = (
            material.density
            * perimeter[-len(wing_model.lift_span) :]
            * wing_model.wing_skin_thickness_m
            * wing_model.dy[-len(wing_model.lift_span) :]
            * 9.81
            * wing_model.load_factor
        )
        expected_force = wing_model.lift_span - expected_weight

        np.testing.assert_allclose(lift, wing_model.lift_span)
        np.testing.assert_allclose(weight, expected_weight)
        np.testing.assert_allclose(force, expected_force)

    def test_torsion_determination(self, wing_model):
        torsion = wing_model.step_torsion_determination(plot=False)

        c_stations_cop = wing_model.chord_stations[-len(wing_model.span_poz) :]
        station_torsion = wing_model.lift_span * c_stations_cop / 4
        expected_torsion = np.cumsum(station_torsion[::-1])[::-1]
        expected_torsion = np.concatenate(
            (
                np.full(
                    len(wing_model.chord_stations) - len(expected_torsion),
                    expected_torsion[0],
                ),
                expected_torsion,
            )
        )

        np.testing.assert_allclose(torsion, expected_torsion)

    def test_wing_rotation(self, wing_model, material):
        torsion = np.array([0.0, 10.0, 20.0, 30.0])

        rotation, rotation_deg = wing_model.step_rotation_of_wing(
            torsion=torsion,
            plot=False,
        )

        perimeter, area = wing_model.perimeter_area_of_section()
        expected_rate = torsion * perimeter / (
            4 * area**2 * material.shear_modulus * wing_model.wing_skin_thickness_m
        )
        expected_rotation = cumulative_trapezoid(
            expected_rate, wing_model.y_stations_chord, initial=0.0
        )

        np.testing.assert_allclose(rotation, expected_rotation)
        np.testing.assert_allclose(rotation_deg, np.degrees(expected_rotation))

    def test_wing_deflection(self, wing_model, material):
        moments = np.array([300.0, 200.0, 100.0, 0.0])

        theta, deflection = wing_model.step_vertical_deflection(
            plot=False,
            moments=moments,
        )

        ix, _ = wing_model.area_moment_inertia()
        curvature = -moments / (material.elastic_modulus * ix)
        expected_theta = cumulative_trapezoid(
            curvature, wing_model.y_stations_chord, initial=0.0
        )
        expected_deflection = cumulative_trapezoid(
            expected_theta, wing_model.y_stations_chord, initial=0.0
        )

        np.testing.assert_allclose(theta, expected_theta)
        np.testing.assert_allclose(deflection, expected_deflection)


    def test_buckling_model(self, wing_model, material):
        buckling_stress = wing_model.buckling_model()

        expected_stress = (
            4
            * np.pi**2
            * material.elastic_modulus
            / (12 * (1 - material.poisson_ratio) ** 2)
            * (wing_model.wing_skin_thickness_m / wing_model.chord_stations)
        )

        np.testing.assert_allclose(buckling_stress, expected_stress)

    def test_wing_stress_per_com_compares_buckling_to_bending(self, wing_model):
        wing_model.step_shear_forces(debug=False, plot=False)

        stress_margin = wing_model.wing_stres_per_com()

        buckling_stress = wing_model.buckling_model()
        moments = wing_model.step_moment(False, False)
        ix, _ = wing_model.area_moment_inertia()
        y_max = wing_model.planform.thickness_to_chord * wing_model.chord_stations
        bending_stress = moments * y_max / ix
        expected_margin = buckling_stress - bending_stress

        np.testing.assert_allclose(stress_margin, expected_margin)


# python -m pytest tests_final/test_wing_geometry.py -v
