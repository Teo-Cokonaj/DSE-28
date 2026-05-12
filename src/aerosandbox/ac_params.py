import aerosandbox.numpy as np

# =============================================================================
# CONSTANTS
# =============================================================================

g = 9.81  # m/s^2

# =============================================================================
# SWEEP CONVERSION HELPERS
# =============================================================================

def sweep_le_to_qc_deg(sweep_le_deg: float, aspect_ratio: float, taper: float) -> float:
    """
    Convert leading-edge sweep angle to quarter-chord sweep angle
    for a trapezoidal lifting surface.
    """
    sweep_le_rad = np.radians(sweep_le_deg)

    sweep_qc_rad = np.arctan(
        np.tan(sweep_le_rad)
        - (1.0 - taper) / (aspect_ratio * (1.0 + taper))
    )

    return np.degrees(sweep_qc_rad)


def sweep_qc_to_le_deg(sweep_qc_deg: float, aspect_ratio: float, taper: float) -> float:
    """
    Convert quarter-chord sweep angle to leading-edge sweep angle
    for a trapezoidal lifting surface.
    """
    sweep_qc_rad = np.radians(sweep_qc_deg)

    sweep_le_rad = np.arctan(
        np.tan(sweep_qc_rad)
        + (1.0 - taper) / (aspect_ratio * (1.0 + taper))
    )

    return np.degrees(sweep_le_rad)


# =============================================================================
# REFERENCE AIRCRAFT PARAMETERS
# =============================================================================
# -----------------------------------------------------------------------------
# DAST ARW-2
# -----------------------------------------------------------------------------

m_DAST = 1060.0  # kg

b_DAST = 5.79  # m
AR_DAST = 10.3
lambda_DAST = 0.40
Lambda_LE_DAST = 28.8  # deg
Lambda_qc_DAST = sweep_le_to_qc_deg(
    sweep_le_deg=Lambda_LE_DAST,
    aspect_ratio=AR_DAST,
    taper=lambda_DAST,
)
tip_twist_DAST = 0.0  # rad


# -----------------------------------------------------------------------------
# NASA X-56A
# -----------------------------------------------------------------------------

m_X = 238.0  # kg, max gross takeoff mass from 525 lb

b_X = 8.53  # m, 28 ft
AR_X = 14.0
lambda_X = 0.46
Lambda_LE_X = 22.0  # deg
Lambda_qc_X = sweep_le_to_qc_deg(
    sweep_le_deg=Lambda_LE_X,
    aspect_ratio=AR_X,
    taper=lambda_X,
)
tip_twist_X = 0.0  # rad


# -----------------------------------------------------------------------------
# Boeing / NASA Transonic Truss-Braced Wing reference
# -----------------------------------------------------------------------------

m_TTBW = 143_164.0 * 0.45359237  # kg

b_TTBW = 170.0 * 0.3048  # m
AR_TTBW = 19.55
lambda_TTBW = 0.30  # preliminary assumption; exact public value not fixed here
Lambda_qc_TTBW = 15.0  # deg, preliminary assumption
Lambda_LE_TTBW = sweep_qc_to_le_deg(
    sweep_qc_deg=Lambda_qc_TTBW,
    aspect_ratio=AR_TTBW,
    taper=lambda_TTBW,
)
tip_twist_TTBW = 0.0  # rad


# -----------------------------------------------------------------------------
# FLEXOP / T-FLEX flexible-wing UAV reference
# -----------------------------------------------------------------------------

m_FLEXOP = 65.0  # kg

b_FLEXOP = 7.07  # m
c_root_FLEXOP = 0.4713  # m
c_tip_FLEXOP = 0.2357  # m

lambda_FLEXOP = c_tip_FLEXOP / c_root_FLEXOP
S_FLEXOP = b_FLEXOP * (c_root_FLEXOP + c_tip_FLEXOP) / 2.0
AR_FLEXOP = b_FLEXOP**2 / S_FLEXOP

Lambda_LE_FLEXOP = 20.0  # deg
Lambda_qc_FLEXOP = sweep_le_to_qc_deg(
    sweep_le_deg=Lambda_LE_FLEXOP,
    aspect_ratio=AR_FLEXOP,
    taper=lambda_FLEXOP,
)
tip_twist_FLEXOP = 0.0  # rad


# =============================================================================
# HUGO AIRCRAFT PARAMETERS
# =============================================================================

m_HUGO = 50.0  # kg

W_over_S_HUGO = 1000.0  # N/m^2

horizontal_stabilizer_distance_from_wing_HUGO = 3.0  # m
vertical_stabilizer_distance_from_wing_HUGO = 3.0  # m
canard_distance_in_front_of_wing = 0.5  # m


# =============================================================================
# HUGO MAIN WING
# =============================================================================

AR_HUGO = 23.0
b_HUGO = 3.36  # m
lambda_HUGO = 0.50

Lambda_LE_HUGO = 15.0  # deg
Lambda_qc_HUGO = sweep_le_to_qc_deg(
    sweep_le_deg=Lambda_LE_HUGO,
    aspect_ratio=AR_HUGO,
    taper=lambda_HUGO,
)

tip_twist_HUGO = 0.0  # rad


# =============================================================================
# HUGO HORIZONTAL STABILIZER
# =============================================================================

HT_AR_HUGO = 3.0
HT_span_HUGO = 0.20  # m
HT_taper_HUGO = 0.50
HT_sweep_quarter_deg_HUGO = 35.0  # deg
HT_tip_twist_rad_HUGO = 0.0  # rad


# =============================================================================
# HUGO VERTICAL STABILIZER
# =============================================================================

VT_AR_HUGO = 1.5
VT_span_HUGO = 0.20  # m
VT_taper_HUGO = 0.50
VT_sweep_quarter_deg_HUGO = 40.0  # deg
VT_tip_twist_rad_HUGO = 0.0  # rad


# =============================================================================
# HUGO CANARD
# =============================================================================

CN_AR_HUGO = 3.0
CN_span_HUGO = 0.20  # m
CN_taper_HUGO = 0.50
CN_sweep_quarter_deg_HUGO = 35.0  # deg
CN_tip_twist_rad_HUGO = 0.0  # rad