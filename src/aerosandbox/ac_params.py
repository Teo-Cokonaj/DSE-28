from dataclasses import dataclass
import aerosandbox.numpy as np

#--------------------------------------CONSTANTS--------------------------------------
g = 9.81  # m/s^2, gravitational acceleration

def sweep_le_to_qc_deg(sweep_le_deg: float, aspect_ratio: float, taper: float) -> float:
    """
    Convert leading-edge sweep angle to quarter-chord sweep angle.

    Parameters
    ----------
    sweep_le_deg : float
        Leading-edge sweep angle [deg].
    aspect_ratio : float
        Aspect ratio [-].
    taper : float
        Taper ratio [-].

    Returns
    -------
    float
        Quarter-chord sweep angle [deg].
    """
    sweep_le = np.radians(sweep_le_deg)
    return np.rad2deg(
        np.arctan(
            np.tan(sweep_le) - (1 - taper) / (aspect_ratio * (1 + taper))
        )
    )


def sweep_qc_to_le_deg(sweep_qc_deg: float, aspect_ratio: float, taper: float) -> float:
    """
    Convert quarter-chord sweep angle to leading-edge sweep angle.

    Parameters
    ----------
    sweep_qc_deg : float
        Quarter-chord sweep angle [deg].
    aspect_ratio : float
        Aspect ratio [-].
    taper : float
        Taper ratio [-].

    Returns
    -------
    float
        Leading-edge sweep angle [deg].
    """
    sweep_qc = np.radians(sweep_qc_deg)
    return np.rad2deg(
        np.arctan(
            np.tan(sweep_qc) + (1 - taper) / (aspect_ratio * (1 + taper))
        )
    )


@dataclass(frozen=True)
class LiftingSurfaceParams:
    """
    Geometric parameters of a trapezoidal lifting surface.

    The span is the full span for symmetric horizontal surfaces such as wings,
    horizontal tails and canards. For vertical tails, use it as the exposed
    vertical span/height.
    """

    name: str
    aspect_ratio: float
    span: float
    taper: float
    sweep_quarter_deg: float
    tip_twist_rad: float = 0.0
    symmetric: bool = True
    airfoil: str | None = None

    @property
    def area(self) -> float:
        """Planform area [m^2]."""
        return self.span**2 / self.aspect_ratio

    @property
    def root_chord(self) -> float:
        """Root chord [m]."""
        return 2 * self.area / (self.span * (1 + self.taper))

    @property
    def tip_chord(self) -> float:
        """Tip chord [m]."""
        return self.taper * self.root_chord

    @property
    def mean_aerodynamic_chord(self) -> float:
        """Mean aerodynamic chord of a trapezoidal lifting surface [m]."""
        return (
            2 / 3 * self.root_chord
            * (1 + self.taper + self.taper**2)
            / (1 + self.taper)
        )

    @property
    def semi_span(self) -> float:
        """Semi-span [m]. For vertical surfaces, this is half of the defined span."""
        return self.span / 2

    @property
    def sweep_quarter_rad(self) -> float:
        """Quarter-chord sweep angle [rad]."""
        return np.radians(self.sweep_quarter_deg)

    @property
    def sweep_le_deg(self) -> float:
        """Leading-edge sweep angle [deg]."""
        return sweep_qc_to_le_deg(
            self.sweep_quarter_deg,
            self.aspect_ratio,
            self.taper,
        )

    @property
    def sweep_le_rad(self) -> float:
        """Leading-edge sweep angle [rad]."""
        return np.radians(self.sweep_le_deg)

    @property
    def tip_le_x_offset(self) -> float:
        """
        Leading-edge x-offset of the tip section relative to the root leading edge [m].

        This is useful for creating an AeroSandbox WingXSec at the tip using
        xyz_le=[tip_le_x_offset, semi_span, z].
        """
        x_tip_qc = self.semi_span * np.tan(self.sweep_quarter_rad)
        return x_tip_qc + 0.25 * self.root_chord - 0.25 * self.tip_chord


@dataclass(frozen=True)
class AircraftParams:
    """Container for aircraft-level parameters and component planforms."""

    name: str
    mass: float
    wing: LiftingSurfaceParams
    wing_loading: float | None = None
    horizontal_stabilizer: LiftingSurfaceParams | None = None
    vertical_stabilizer: LiftingSurfaceParams | None = None
    canard: LiftingSurfaceParams | None = None
    horizontal_stabilizer_distance_from_wing: float | None = None
    vertical_stabilizer_distance_from_wing: float | None = None
    canard_distance_in_front_of_wing: float | None = None

    @property
    def weight(self) -> float:
        """Aircraft weight [N]."""
        return self.mass * g

    @property
    def wing_area_from_geometry(self) -> float:
        """Wing area from span and aspect ratio [m^2]."""
        return self.wing.area

    @property
    def wing_area_from_loading(self) -> float | None:
        """Wing area implied by W/S [m^2], if wing_loading is defined."""
        if self.wing_loading is None:
            return None
        return self.weight / self.wing_loading


#--------------------------------------AIRCRAFT PARAMETER OBJECTS--------------------------------------

DAST_ARW2 = AircraftParams(
    name="DAST ARW-2",
    mass=1060,  # kg
    wing=LiftingSurfaceParams(
        name="DAST ARW-2 wing",
        aspect_ratio=10.3,
        span=5.79,  # m
        taper=0.4,
        sweep_quarter_deg=sweep_le_to_qc_deg(28.8, 10.3, 0.4),
        tip_twist_rad=0.0,
        symmetric=True,
    ),
)

X56A = AircraftParams(
    name="NASA X-56A",
    mass=238,  # kg
    wing=LiftingSurfaceParams(
        name="X-56A wing",
        aspect_ratio=14.0,
        span=8.53,  # m
        taper=0.46,
        sweep_quarter_deg=sweep_le_to_qc_deg(22.0, 14.0, 0.46),
        tip_twist_rad=0.0,
        symmetric=True,
    ),
)

BOEING_TTBW = AircraftParams(
    name="Boeing/NASA Mach 0.745 Transonic Truss-Braced Wing",
    mass=143164.0 * 0.45359237,  # kg, full-scale reference weight
    wing=LiftingSurfaceParams(
        name="Boeing/NASA TTBW wing",
        aspect_ratio=19.55,
        span=170.0 * 0.3048,  # m
        taper=0.3,  # assumed preliminary value; exact public value not found
        sweep_quarter_deg=15.0,  # assumed preliminary value; exact public value not found
        tip_twist_rad=0.0,
        symmetric=True,
    ),
)

FLEXOP = AircraftParams(
    name="FLEXOP / T-FLEX flexible-wing UAV demonstrator",
    mass=65.0,  # kg
    wing=LiftingSurfaceParams(
        name="FLEXOP wing",
        aspect_ratio=7.07**2 / (7.07 * (0.4713 + 0.2357) / 2.0),
        span=7.07,  # m
        taper=0.2357 / 0.4713,
        sweep_quarter_deg=sweep_le_to_qc_deg(
            20.0,
            7.07**2 / (7.07 * (0.4713 + 0.2357) / 2.0),
            0.2357 / 0.4713,
        ),
        tip_twist_rad=0.0,
        symmetric=True,
        airfoil="try6",
    ),
)

HUGO = AircraftParams(
    name="HUGO",
    mass=50,  # kg
    wing_loading=1000,  # N/m^2
    wing=LiftingSurfaceParams(
        name="HUGO wing",
        aspect_ratio=23.0,
        span=3.36,  # m
        taper=0.5,
        sweep_quarter_deg=sweep_le_to_qc_deg(15.0, 23.0, 0.5),
        tip_twist_rad=0.0,
        symmetric=True,
        airfoil="NASA SC(2)-0012",
    ),
    horizontal_stabilizer=LiftingSurfaceParams(
        name="HUGO horizontal stabilizer",
        aspect_ratio=3.0,
        span=0.5,  # m
        taper=1.0,
        sweep_quarter_deg=45.0,
        tip_twist_rad=0.0,
        symmetric=True,
    ),
    vertical_stabilizer=LiftingSurfaceParams(
        name="HUGO vertical stabilizer",
        aspect_ratio=1.5,
        span=0.5,  # m, vertical height/exposed span
        taper=1.0,
        sweep_quarter_deg=45.0,
        tip_twist_rad=0.0,
        symmetric=False,
    ),
    canard=LiftingSurfaceParams(
        name="HUGO canard",
        aspect_ratio=3.0,
        span=0.5,  # m
        taper=1.0,
        sweep_quarter_deg=45.0,
        tip_twist_rad=0.0,
        symmetric=True,
    ),
    horizontal_stabilizer_distance_from_wing=3.0,  # m
    vertical_stabilizer_distance_from_wing=3.0,  # m
    canard_distance_in_front_of_wing=0.5,  # m
)


#--------------------------------------BACKWARD-COMPATIBLE ALIASES--------------------------------------
# These keep older scripts working while allowing aircraft_model.py to migrate
# to the structured objects above.

# DAST ARW-2
b_DAST = DAST_ARW2.wing.span
AR_DAST = DAST_ARW2.wing.aspect_ratio
lambda_DAST = DAST_ARW2.wing.taper
Lambda_LE_DAST = DAST_ARW2.wing.sweep_le_deg
Lambda_qc_DAST = DAST_ARW2.wing.sweep_quarter_deg  # degrees
tip_twist_DAST = DAST_ARW2.wing.tip_twist_rad
m_DAST = DAST_ARW2.mass

# X-56A
b_X = X56A.wing.span
AR_X = X56A.wing.aspect_ratio
lambda_X = X56A.wing.taper
Lambda_LE_X = X56A.wing.sweep_le_deg
Lambda_qc_X = X56A.wing.sweep_quarter_deg  # degrees
tip_twist_X = X56A.wing.tip_twist_rad
m_X = X56A.mass

# HUGO wing
b_HUGO = HUGO.wing.span
AR_HUGO = HUGO.wing.aspect_ratio
lambda_HUGO = HUGO.wing.taper
Lambda_LE_HUGO = HUGO.wing.sweep_le_deg
Lambda_qc_HUGO = HUGO.wing.sweep_quarter_deg  # degrees
tip_twist_HUGO = HUGO.wing.tip_twist_rad
m_HUGO = HUGO.mass
W_over_S_HUGO = HUGO.wing_loading
horizontal_stabilizer_distance_from_wing_HUGO = HUGO.horizontal_stabilizer_distance_from_wing
vertical_stabilizer_distance_from_wing_HUGO = HUGO.vertical_stabilizer_distance_from_wing
canard_distance_in_front_of_wing = HUGO.canard_distance_in_front_of_wing

# HUGO horizontal stabilizer
HT_AR_HUGO = HUGO.horizontal_stabilizer.aspect_ratio
HT_span_HUGO = HUGO.horizontal_stabilizer.span
HT_sweep_quarter_deg_HUGO = HUGO.horizontal_stabilizer.sweep_quarter_deg
HT_taper_HUGO = HUGO.horizontal_stabilizer.taper
HT_tip_twist_rad_HUGO = HUGO.horizontal_stabilizer.tip_twist_rad

# HUGO vertical stabilizer
VT_AR_HUGO = HUGO.vertical_stabilizer.aspect_ratio
VT_span_HUGO = HUGO.vertical_stabilizer.span
VT_sweep_quarter_deg_HUGO = HUGO.vertical_stabilizer.sweep_quarter_deg
VT_taper_HUGO = HUGO.vertical_stabilizer.taper
VT_tip_twist_rad_HUGO = HUGO.vertical_stabilizer.tip_twist_rad

# HUGO canard
CN_AR_HUGO = HUGO.canard.aspect_ratio
CN_span_HUGO = HUGO.canard.span
CN_sweep_quarter_deg_HUGO = HUGO.canard.sweep_quarter_deg
CN_taper_HUGO = HUGO.canard.taper
CN_tip_twist_rad_HUGO = HUGO.canard.tip_twist_rad