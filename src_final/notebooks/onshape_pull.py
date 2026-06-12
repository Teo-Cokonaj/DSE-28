import requests
import re
import json
import os

# ===================================================================
# CONFIG — Toggle what gets fetched from the API
# ===================================================================
UPDATE_MASSES = False   # True → hit assembly API (~80 calls). False → use mass_cache.json
MASS_CACHE_FILE = "mass_cache.json"

# ===================================================================
# ONSHAPE API CREDENTIALS
# ===================================================================
API_URL = "https://cad.onshape.com"
ACCESS_KEY = 'on_wkiWin3a4Nq7pTbfVt7pB'
SECRET_KEY = '0vS06G7KDpVeP6wsFl2j4giQN93UbakaPwhqGmUmIPeR1sVm'

# Assembly API uses separate keys (from extractandsave.py)
ASSEMBLY_ACCESS_KEY = "on_ZZzfBxwa3TC6GxkWekaqt"
ASSEMBLY_SECRET_KEY = "tS7EE3Ilnx6XvREH1Ncm2bT3fFc8tfcpuApd3MbJf9boA2KH"

# --- TARGET IDs ---
DID = "e17cbed2e815359ba964f636"
WID = "0bc6fdd770562c4aa0c2a839"
ASSEMBLY_WID = "0bc6fdd770562c4aa0c2a839"
ASSEMBLY_EID = "1f24790f90e799bbc1eb8f34"

FUSELAGE_STUDIO_EID = "cd8303f96be0e5a01a796829"
VARIABLE_STUDIO_EID = "d1aeb957b769ef00d412a1b2"

HEADERS_JSON = {"Accept": "application/vnd.onshape.v2+json"}
HEADERS_POST = {
    "Accept": "application/vnd.onshape.v2+json",
    "Content-Type": "application/json",
}
HEADERS_ASSEMBLY = {
    "Accept": "application/vnd.onshape.v1+json",
    "Content-Type": "application/json",
}


# ---------------------------------------------------------------------------
# 1. VARIABLE STUDIO – get all variables with parsed expressions
# ---------------------------------------------------------------------------

def parse_expression(expr):
    """
    Parse an Onshape expression string into a (value_float, unit_str) tuple.
    e.g. "250 mm" → (250.0, "mm"), "15 deg" → (15.0, "deg"), "0.5" → (0.5, "")
    For formulas like "sqrt(#CanardAspectRatio*#CanardArea)" → returns (None, expr)
    """
    if not expr or not isinstance(expr, str):
        return None, str(expr) if expr else ""

    expr = expr.strip()

    # If expression contains # references, it's a formula we can't evaluate here
    if "#" in expr:
        return None, expr

    # Try: "<number> <unit>"
    m = re.match(r"^([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)\s*(.*)$", expr)
    if m:
        try:
            val = float(m.group(1))
            unit = m.group(2).strip()
            return val, unit
        except ValueError:
            pass

    # Try bare number
    try:
        return float(expr), ""
    except ValueError:
        return None, expr


def fetch_variable_studio():
    """Pull every variable from the Variable Studio and parse expressions."""
    url = f"{API_URL}/api/variables/d/{DID}/w/{WID}/e/{VARIABLE_STUDIO_EID}/variables"
    r = requests.get(url, auth=(ACCESS_KEY, SECRET_KEY), headers=HEADERS_JSON)

    if r.status_code != 200:
        raise Exception(f"Variable Studio API Error {r.status_code}: {r.text}")

    data = r.json()
    variables = []

    for block in data:
        for item in block.get("variables", []):
            name = item.get("name", "")
            expr = item.get("expression", "")
            vtype = item.get("type", "")
            desc = item.get("description", "")

            val, unit = parse_expression(expr)

            variables.append({
                "name": name,
                "type": vtype,
                "expression": expr,
                "value": val,
                "unit": unit,
                "description": desc,
            })

    return variables


# ---------------------------------------------------------------------------
# 2. FUSELAGE PART STUDIO – get measurement features + evaluate via FS
# ---------------------------------------------------------------------------

def fetch_measurement_features():
    """Discover measureDistance feature names from the Fuselage Part Studio."""
    url = f"{API_URL}/api/partstudios/d/{DID}/w/{WID}/e/{FUSELAGE_STUDIO_EID}/features"
    r = requests.get(url, auth=(ACCESS_KEY, SECRET_KEY), headers=HEADERS_JSON)

    if r.status_code != 200:
        raise Exception(f"Features API Error {r.status_code}: {r.text}")

    data = r.json()
    measurements = []

    for f in data.get("features", []):
        if f.get("featureType") == "measureDistance":
            name = ""
            for p in f.get("parameters", []):
                if p.get("parameterId") == "name":
                    name = p.get("value", "?")
            measurements.append(name)

    return measurements


# Variable Studio formula variables that also need FS evaluation (resolved via Fuselage studio context)
VS_FORMULA_VARS = ["Tailcone_X", "Front_Gear_Extension_Max", "Front_Gear_Extension_Min"]


def evaluate_measurements(names):
    """Run a FeatureScript eval to get computed values for the named measurement variables."""
    if not names:
        return {}

    # Include VS formula variables alongside measurement feature names
    all_names = list(set(names + VS_FORMULA_VARS))

    # Build FS that reads each variable with getVariable
    name_literals = ", ".join(f'"{n}"' for n in all_names)
    script = f'''function(context is Context, queries is map) {{
    var names = [{name_literals}];
    var vals = {{}};
    for (var name in names) {{
        try {{
            var v = getVariable(context, name);
            vals[name] = v;
        }} catch {{
            vals[name] = undefined;
        }}
    }}
    return vals;
}}'''

    url = f"{API_URL}/api/partstudios/d/{DID}/w/{WID}/e/{FUSELAGE_STUDIO_EID}/featurescript"
    r = requests.post(url, auth=(ACCESS_KEY, SECRET_KEY), headers=HEADERS_POST, json={"script": script})

    if r.status_code != 200:
        raise Exception(f"FeatureScript eval error {r.status_code}: {r.text}")

    data = r.json()

    # Check for errors
    for n in data.get("notices", []):
        if n.get("level") == "ERROR":
            print(f"  [FS ERROR] {n.get('message')}")

    # Parse the result map: BTFSValueMap with value = list of BTFSValueMapEntry
    result = {}
    raw_map = data.get("result", {})
    entries = raw_map.get("value", []) if raw_map else []

    for entry in entries:
        key_obj = entry.get("key", {})
        val_obj = entry.get("value", {})

        key = key_obj.get("value", "?")
        value = val_obj.get("value")
        units = val_obj.get("unitToPower", {})

        unit_str = format_units(units)

        result[key] = {"value": value, "unit": unit_str}

    return result


def format_units(unit_to_power):
    """Convert Onshape unit map like {'METER': 2} → 'm²', {'METER': 1} → 'm'."""
    symbols = {"METER": "m", "RADIAN": "rad", "SECOND": "s", "KILOGRAM": "kg"}
    parts = []
    for unit, power in unit_to_power.items():
        sym = symbols.get(unit, unit.lower())
        if power == 1:
            parts.append(sym)
        elif power == 2:
            parts.append(f"{sym}²")
        elif power == 3:
            parts.append(f"{sym}³")
        else:
            parts.append(f"{sym}^{power}")
    return " ".join(parts) if parts else ""


# ---------------------------------------------------------------------------
# 3. ASSEMBLY MASS PROPERTIES – fetch or cache component masses + CGs
# ---------------------------------------------------------------------------

def _assembly_get(url, params=None):
    """GET request to the Onshape assembly API."""
    r = requests.get(
        url,
        auth=(ASSEMBLY_ACCESS_KEY, ASSEMBLY_SECRET_KEY),
        headers=HEADERS_ASSEMBLY,
        params=params,
    )
    if r.status_code != 200:
        return None
    return r.json()


def _extract_vertices(node, vertices_list):
    """Recursively extract vertex coordinates from tessellated face data."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "vertices" and isinstance(v, list):
                for item in v:
                    if isinstance(item, list) and len(item) >= 3:
                        vertices_list.extend([float(item[0]), float(item[1]), float(item[2])])
                    elif isinstance(item, (int, float)):
                        vertices_list.append(float(item))
                    elif isinstance(item, dict):
                        if "x" in item and "y" in item and "z" in item:
                            vertices_list.extend([float(item["x"]), float(item["y"]), float(item["z"])])
                        else:
                            vals = list(item.values())
                            if len(vals) >= 3:
                                vertices_list.extend([float(vals[0]), float(vals[1]), float(vals[2])])
            else:
                _extract_vertices(v, vertices_list)
    elif isinstance(node, list):
        for item in node:
            _extract_vertices(item, vertices_list)


def fetch_mass_properties():
    """
    Walk the full assembly, fetch mass/CG for every part, and return
    a list of dicts: [{name, mass, cg_x, cg_y, cg_z}, ...].
    Saves to mass_cache.json after fetching.
    """
    BASE = f"{API_URL}/api/v10"

    assembly_url = f"{BASE}/assemblies/d/{DID}/w/{ASSEMBLY_WID}/e/{ASSEMBLY_EID}"
    assembly_data = _assembly_get(assembly_url)

    if not assembly_data:
        raise Exception("Failed to retrieve assembly data.")

    instances_dict = {}
    if "rootAssembly" in assembly_data:
        for inst in assembly_data["rootAssembly"].get("instances", []):
            instances_dict[inst["id"]] = inst
    for sub in assembly_data.get("subAssemblies", []):
        for inst in sub.get("instances", []):
            instances_dict[inst["id"]] = inst

    occurrences = assembly_data.get("rootAssembly", {}).get("occurrences", [])
    print(f"  → Found {len(occurrences)} occurrences, fetching mass properties...")

    part_cache = {}
    components = []

    for i, occ in enumerate(occurrences):
        path = occ.get("path", [])
        if not path:
            continue

        inst_id = path[-1]
        inst = instances_dict.get(inst_id)

        if not inst or inst.get("type") != "Part":
            continue

        name = inst.get("name", "Unknown Part")
        part_id = inst.get("partId")
        doc_id = inst.get("documentId")
        elem_id = inst.get("elementId")
        m_id = inst.get("documentMicroversion")
        config = inst.get("configuration", "")

        transform = occ.get("transform", [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1])
        cache_key = f"{doc_id}_{elem_id}_{part_id}_{config}"

        if cache_key not in part_cache:
            wvm = "m" if m_id else "w"
            wvmid = m_id if m_id else ASSEMBLY_WID
            params = {"configuration": config} if config else {}
            params["useMassPropertyOverrides"] = "true"

            # Fetch mass properties
            mass_url = f"{BASE}/parts/d/{doc_id}/{wvm}/{wvmid}/e/{elem_id}/partid/{part_id}/massproperties"
            mass_data = _assembly_get(mass_url, params)

            mass = 0.0
            cx, cy, cz = 0.0, 0.0, 0.0
            if mass_data and "bodies" in mass_data:
                body_data = mass_data["bodies"].get(part_id, {})
                mass = body_data.get("mass", [0.0])[0]
                centroid = body_data.get("centroid", [0.0, 0.0, 0.0])
                if len(centroid) >= 3:
                    cx, cy, cz = centroid[0], centroid[1], centroid[2]

            part_cache[cache_key] = {"mass": mass, "cx": cx, "cy": cy, "cz": cz}

        props = part_cache[cache_key]

        # Transform part-local CG into assembly coordinates
        tx, ty, tz = transform[3], transform[7], transform[11]
        cg_x = (transform[0] * props["cx"]) + (transform[1] * props["cy"]) + (transform[2] * props["cz"]) + tx
        cg_y = (transform[4] * props["cx"]) + (transform[5] * props["cy"]) + (transform[6] * props["cz"]) + ty
        cg_z = (transform[8] * props["cx"]) + (transform[9] * props["cy"]) + (transform[10] * props["cz"]) + tz

        components.append({
            "name": name,
            "mass": props["mass"],
            "cg_x": cg_x,
            "cg_y": cg_y,
            "cg_z": cg_z,
        })

        if (i + 1) % 10 == 0:
            print(f"    ... processed {i + 1}/{len(occurrences)} occurrences")

    # Save cache
    with open(MASS_CACHE_FILE, "w") as f:
        json.dump(components, f, indent=2)
    print(f"  → Mass data cached to {MASS_CACHE_FILE}")

    return components


def load_cached_masses():
    """Load mass data from the JSON cache file."""
    if not os.path.exists(MASS_CACHE_FILE):
        raise FileNotFoundError(
            f"{MASS_CACHE_FILE} not found. Set UPDATE_MASSES = True to fetch from API first."
        )
    with open(MASS_CACHE_FILE) as f:
        components = json.load(f)
    print(f"  → Loaded {len(components)} components from {MASS_CACHE_FILE}")
    return components


# ---------------------------------------------------------------------------
# 3b. CG COMPUTATIONS
# ---------------------------------------------------------------------------

def is_fuel_component(name):
    """Return True if the component is fuel mass (not the bag itself)."""
    return name.startswith("Fuel <")


def compute_cg(components, include_fuel_1=True, include_fuel_2=True):
    """
    Compute total mass and CG given a list of components.
    Excludes suppressed parts and can exclude fuel tanks to find CG bounds.
    Returns (total_mass, cg_x, cg_y, cg_z).
    """
    total_mass = 0.0
    moment_x = 0.0
    moment_y = 0.0
    moment_z = 0.0

    # Define parts to universally ignore (substring match ignores instance numbers)
    EXCLUDED_PARTS = ["Canard", "Wing_Port_Cover", "Wing Port Foam"]

    for c in components:
        mass = c["mass"]
        name = c["name"]

        # 1. Skip universally excluded parts (suppressed in CAD)
        if any(excluded in name for excluded in EXCLUDED_PARTS):
            continue

        # 2. Skip fuel tanks based on flags (using substring match for robustness)
        if "Fuel" in name and "<1>" in name and not include_fuel_1:
            continue
        if "Fuel" in name and "<2>" in name and not include_fuel_2:
            continue

        total_mass += mass
        moment_x += mass * c["cg_x"]
        moment_y += mass * c["cg_y"]
        moment_z += mass * c["cg_z"]

    if total_mass == 0:
        return 0, 0, 0, 0

    return total_mass, moment_x / total_mass, moment_y / total_mass, moment_z / total_mass


def compute_cg_scenarios(components):
    """
    Compute CG for 3 fuel scenarios:
      - Both tanks full → total mass, full CG
      - Tank 1 full, Tank 2 empty → CG forward
      - Tank 1 empty, Tank 2 full → CG aft
    Returns dict with mass, x_cg_min, x_cg_max, z_cg (from full config).
    """
    # Both full
    mass_full, cg_x_full, cg_y_full, cg_z_full = compute_cg(components, True, True)

    # Tank 1 full, Tank 2 empty
    _, cg_x_t1_only, _, _ = compute_cg(components, True, False)

    # Tank 1 empty, Tank 2 full
    _, cg_x_t2_only, _, _ = compute_cg(components, False, True)

    # CG min/max — min is most forward, max is most aft
    x_cg_min = min(cg_x_t1_only, cg_x_t2_only)
    x_cg_max = max(cg_x_t1_only, cg_x_t2_only)

    # Extract individual fuel masses for reference (using substring match)
    fuel_1_mass = sum(c["mass"] for c in components if "Fuel" in c["name"] and "<1>" in c["name"])
    fuel_2_mass = sum(c["mass"] for c in components if "Fuel" in c["name"] and "<2>" in c["name"])
    fuel_total = fuel_1_mass + fuel_2_mass

    return {
        "mass": mass_full,
        "fuel_mass": fuel_total,
        "fuel_1_mass": fuel_1_mass,
        "fuel_2_mass": fuel_2_mass,
        "x_cg_full": cg_x_full,
        "z_cg_full": cg_z_full,
        "x_cg_min": x_cg_min,
        "x_cg_max": x_cg_max,
        "x_cg_t1_only": cg_x_t1_only,
        "x_cg_t2_only": cg_x_t2_only,
    }

# ---------------------------------------------------------------------------
# 4. PRETTY PRINT
# ---------------------------------------------------------------------------

def print_section(title, width=78):
    print()
    print("=" * width)
    print(f" {title}")
    print("=" * width)


def print_variable_table(variables):
    """Print Variable Studio variables grouped by section headers."""
    sections = {}
    current_section = "General"

    for v in variables:
        desc = v["description"]
        is_header = (
            v["type"] == "ANY"
            and desc.strip().startswith("=")
            and v["value"] is None
        )

        if is_header:
            current_section = v["name"].replace("_", " ")
            continue

        if current_section not in sections:
            sections[current_section] = []
        sections[current_section].append(v)

    for section_name, section_vars in sections.items():
        print(f"\n  ── {section_name} ──")
        for v in section_vars:
            name = v["name"]
            val = v["value"]
            expr = v["expression"]
            unit = v["unit"]
            desc = v["description"]

            if val is not None:
                if abs(val) >= 100:
                    val_str = f"{val:.2f} {unit}"
                elif abs(val) >= 1:
                    val_str = f"{val:.4f} {unit}"
                else:
                    val_str = f"{val:.6f} {unit}"
            else:
                val_str = f"[formula] {expr}"

            if desc and not desc.strip().startswith("="):
                val_str += f"  ({desc})"

            print(f"    {name:<38} {val_str}")


def print_measurement_table(measurements):
    """Print evaluated Fuselage Part Studio measurements."""
    for name, info in sorted(measurements.items()):
        val = info["value"]
        unit = info["unit"]
        if val is not None:
            if abs(val) < 0.01:
                val_str = f"{val:.8f} {unit}"
            elif abs(val) < 1:
                val_str = f"{val:.6f} {unit}"
            else:
                val_str = f"{val:.6f} {unit}"
        else:
            val_str = "[could not evaluate]"
        print(f"    {name:<38} {val_str}")


def print_derived_table(derived):
    """Print computed derived values."""
    for name, val, unit, formula in derived:
        if val is not None:
            if unit == "m":
                val_str = f"{val:.6f} m  ({val * 1000:.2f} mm)"
            elif unit == "kg":
                val_str = f"{val:.4f} kg"
            elif unit == "deg":
                val_str = f"{val:.4f} deg"
            elif unit == "m²":
                val_str = f"{val:.6f} m²  ({val * 1e6:.1f} mm²)"
            else:
                val_str = f"{val:.6f} {unit}"
        else:
            val_str = "[missing input]"
        print(f"    {name:<45} {val_str}")
        if formula:
            print(f"    {'':45} ← {formula}")
        print()


# ---------------------------------------------------------------------------
# 5. DERIVED VALUES – computed from all sources
# ---------------------------------------------------------------------------

def lookup_var(variables, name):
    """Look up a variable by exact name. Returns (value_m_or_none, expression_str, unit_str)."""
    for v in variables:
        if v["name"] == name:
            val = v["value"]
            unit = v["unit"]
            expr = v["expression"]
            if val is not None:
                if unit == "mm":
                    return val / 1000.0, expr, "m"
                elif unit == "deg":
                    return val, expr, "deg"
                else:
                    return val, expr, unit
            return None, expr, unit
    return None, "", ""


def lookup_meas(measurements, name):
    """Look up an evaluated measurement by name. Returns value in SI (meters)."""
    info = measurements.get(name, {})
    return info.get("value")


def compute_derived(variables, measurements, cg_data):
    """Compute all derived values. Returns list of (name, value, unit, formula_str)."""
    derived = []

    # --- Helper lookups (Variable Studio) ---
    Front_Strut_Height,          _, _ = lookup_var(variables, "Front_Strut_Height")
    Rear_Strut_Height,           _, _ = lookup_var(variables, "Rear_Strut_Height")
    Rear_Strut_height_2,         _, _ = lookup_var(variables, "Rear_Strut_height_2")
    Wheel_Diameter,              _, _ = lookup_var(variables, "Wheel_Diameter")
    WingPortDistance,             _, _ = lookup_var(variables, "WingPortDistance")
    WingPortWidth,                _, _ = lookup_var(variables, "WingPortWidth")
    CanardPortXLoc,               _, _ = lookup_var(variables, "CanardPortXLoc")
    CanardPortWidth,              _, _ = lookup_var(variables, "CanardPortWidth")
    Front_Strut_Diameter,        _, _ = lookup_var(variables, "Front_Strut_Diameter")
    Rear_Strut_Diameter,         _, _ = lookup_var(variables, "Rear_Strut_Diameter")
    Engine_diameter,             _, _ = lookup_var(variables, "engine_diameter")
    Front_Gear_Extension_Max,    _, _ = lookup_var(variables, "Front_Gear_Extension_Max")
    Front_Gear_Extension_Min,    _, _ = lookup_var(variables, "Front_Gear_Extension_Min")

    # Override with FS-evaluated values if available (these may be formulas in VS)
    fs_ext_max = lookup_meas(measurements, "Front_Gear_Extension_Max")
    fs_ext_min = lookup_meas(measurements, "Front_Gear_Extension_Min")
    if fs_ext_max is not None:
        Front_Gear_Extension_Max = fs_ext_max
    if fs_ext_min is not None:
        Front_Gear_Extension_Min = fs_ext_min

    # --- Helper lookups (Fuselage measurements + FS-evaluated VS formulas) ---
    Front_Gear_Unexposed       = lookup_meas(measurements, "Front_Gear_Unexposed")
    Front_Landing_Gear_Hinge_Z = lookup_meas(measurements, "Front_Landing_Gear_Hinge_Z")
    Z_wing_LE_Abs              = lookup_meas(measurements, "Z_wing_LE_Abs")
    X_LE_Tail                  = lookup_meas(measurements, "X_LE_Tail")
    Z_LE_Tail                  = lookup_meas(measurements, "Z_LE_Tail")
    Z_TailCone                 = lookup_meas(measurements, "Z_TailCone")
    Tailcone_X                 = lookup_meas(measurements, "Tailcone_X")

    # ===================================================================
    # AXLE Z DATUM  (used for all Z-from-axle conversions)
    # z_offset = Front_Landing_Gear_Hinge_Z + Front_Strut_Height
    #          + (Front_Gear_Extension_Max - Front_Gear_Extension_Min)
    # ===================================================================
    z_offset = None
    if all(v is not None for v in [
        Front_Landing_Gear_Hinge_Z, Front_Strut_Height,
        Front_Gear_Extension_Max, Front_Gear_Extension_Min
    ]):
        z_offset = (Front_Landing_Gear_Hinge_Z
                    + Front_Strut_Height
                    + (Front_Gear_Extension_Max - Front_Gear_Extension_Min))

    # ===================================================================
    # FUSELAGE
    # ===================================================================
    derived.append(("--- FUSELAGE ---", None, "", ""))

    Wetted_Area = lookup_meas(measurements, "Wetted_Area")
    if Wetted_Area is not None:
        derived.append(("fuselage.surface_wetted", Wetted_Area, "m²",
                         "Wetted_Area from Fuselage Studio"))

    FuselageLength, _, _ = lookup_var(variables, "FuselageLength")
    if FuselageLength is not None:
        derived.append(("fuselage.length_total", FuselageLength, "m",
                         "FuselageLength from Variable Studio"))

    FuselageHeight, _, _ = lookup_var(variables, "FuselageHeight")
    if FuselageHeight is not None:
        derived.append(("fuselage.diameter_max", FuselageHeight, "m",
                         "FuselageHeight from Variable Studio"))

    derived.append(("fuselage.upsweep", 0.0, "deg", "0 (no upsweep)"))

    Base_Area = lookup_meas(measurements, "Base_Area")
    if Base_Area is not None:
        derived.append(("fuselage.base_area", Base_Area, "m²",
                         "Base_Area from Fuselage Studio"))

    # ===================================================================
    # LANDING GEAR
    # ===================================================================
    derived.append(("--- LANDING GEAR ---", None, "", ""))

    # Wheel specs (shared)
    derived.append(("Wheel_Width", 0.025, "m", "25 mm (fixed)"))
    if Wheel_Diameter is not None:
        derived.append(("Wheel_Diameter", Wheel_Diameter, "m", "from Variable Studio"))

    # Nose gear
    if Front_Strut_Height is not None and Front_Gear_Unexposed is not None:
        val = Front_Strut_Height - Front_Gear_Unexposed
        derived.append(("nose_gear.exposed_height", val, "m",
                         f"Front_Strut_Height - Front_Gear_Unexposed"))
    if Wheel_Diameter is not None:
        derived.append(("nose_gear.wheel_diameter", Wheel_Diameter, "m", "from Variable Studio"))
    derived.append(("nose_gear.wheel_width", 0.025, "m", "25 mm (fixed)"))
    if Front_Strut_Diameter is not None:
        derived.append(("nose_gear.strut_width", Front_Strut_Diameter, "m",
                         "Front_Strut_Diameter from Variable Studio"))

    # Main gear
    if Rear_Strut_Height is not None and Rear_Strut_height_2 is not None:
        val = Rear_Strut_Height + Rear_Strut_height_2
        derived.append(("main_gear.exposed_height", val, "m",
                         f"Rear_Strut_Height + Rear_Strut_height_2"))
    if Wheel_Diameter is not None:
        derived.append(("main_gear.wheel_diameter", Wheel_Diameter, "m", "from Variable Studio"))
    derived.append(("main_gear.wheel_width", 0.025, "m", "25 mm (fixed)"))
    if Rear_Strut_Diameter is not None:
        derived.append(("main_gear.strut_width", Rear_Strut_Diameter, "m",
                         "Rear_Strut_Diameter from Variable Studio"))

    # Gear bays — all zero per user
    derived.append(("gear_bay.surface_wetted", 0.0, "m²", "0 (not modeled)"))
    derived.append(("gear_bay.length", 0.0, "m", "0 (not modeled)"))
    derived.append(("gear_bay.diameter", 0.0, "m", "0 (not modeled)"))

    # ===================================================================
    # ENGINE BAY
    # ===================================================================
    derived.append(("--- ENGINE BAY ---", None, "", ""))

    engine_wetted = 83744.32631 / 1e6  # mm² → m²
    derived.append(("engine_bay.surface_wetted", engine_wetted, "m²",
                     "83744.32631 mm² (user provided)"))
    derived.append(("engine_bay.length", 0.172, "m", "172 mm (user provided)"))
    if Engine_diameter is not None:
        derived.append(("engine_bay.diameter", Engine_diameter, "m",
                         f"engine_diameter from Variable Studio"))

    # ===================================================================
    # FIXED PARAMETERS
    # ===================================================================
    derived.append(("--- FIXED PARAMETERS ---", None, "", ""))

    # --- Axle Z Datum ---
    if z_offset is not None:
        derived.append(("Axle_Z_Datum", z_offset, "m",
                         f"Hinge_Z ({Front_Landing_Gear_Hinge_Z:.4f}) + Strut_H ({Front_Strut_Height:.4f})"
                         f" + (Ext_Max ({Front_Gear_Extension_Max:.4f}) - Ext_Min ({Front_Gear_Extension_Min:.4f}))"))

    # --- Mass & CG ---
    if cg_data:
        derived.append(("fixed.mass", cg_data["mass"], "kg",
                         f"Total assembly mass (all components + both fuel tanks)"))
        derived.append(("fixed.fuel_mass", cg_data["fuel_mass"], "kg",
                         f"Fuel 1 ({cg_data['fuel_1_mass']:.2f} kg) + Fuel 2 ({cg_data['fuel_2_mass']:.2f} kg)"))
        derived.append(("fixed.x_cg_min", cg_data["x_cg_min"], "m",
                         f"T1 full/T2 empty={cg_data['x_cg_t1_only']:.5f}, T2 full/T1 empty={cg_data['x_cg_t2_only']:.5f}"))
        derived.append(("fixed.x_cg_max", cg_data["x_cg_max"], "m",
                         f"T1 full/T2 empty={cg_data['x_cg_t1_only']:.5f}, T2 full/T1 empty={cg_data['x_cg_t2_only']:.5f}"))

    if cg_data and z_offset is not None:
        z_cg_from_axle = cg_data["z_cg_full"] + z_offset
        derived.append(("fixed.z_cg", z_cg_from_axle, "m",
                         f"Assembly CG z ({cg_data['z_cg_full']:.6f}) + Axle_Z_Datum ({z_offset:.6f})"))

    # --- Tail cone ---
    if Tailcone_X is not None:
        derived.append(("fixed.x_tail_cone", Tailcone_X, "m",
                         "Tailcone_X from Variable Studio (FS evaluated)"))

    if Z_TailCone is not None and z_offset is not None:
        # Z_TailCone is below origin → negate, then add axle datum offset
        z_tailcone_from_axle = -Z_TailCone + z_offset
        derived.append(("fixed.z_tail_cone", z_tailcone_from_axle, "m",
                         f"-Z_TailCone ({Z_TailCone:.6f}) + Axle_Z_Datum ({z_offset:.6f})"))

    # --- Z positions (all from axle datum) ---
    if Z_wing_LE_Abs is not None and z_offset is not None:
        val = Z_wing_LE_Abs + z_offset
        derived.append(("fixed.z_wing (from axle datum)", val, "m",
                         f"Z_wing_LE_Abs ({Z_wing_LE_Abs:.6f}) + Axle_Z_Datum ({z_offset:.6f})"))

    if Z_LE_Tail is not None and z_offset is not None:
        val = Z_LE_Tail + z_offset
        derived.append(("fixed.z_LE_tail (from axle datum)", val, "m",
                         f"Z_LE_Tail ({Z_LE_Tail:.6f}) + Axle_Z_Datum ({z_offset:.6f})"))

    # --- X positions ---
    if CanardPortXLoc is not None and CanardPortWidth is not None:
        val = CanardPortXLoc + CanardPortWidth / 2
        derived.append(("fixed.x_LE_canard", val, "m",
                         f"CanardPortXLoc + CanardPortWidth/2"))

    if WingPortDistance is not None and WingPortWidth is not None:
        val = WingPortDistance + WingPortWidth / 2
        derived.append(("fixed.x_LE_wing", val, "m",
                         f"WingPortDistance + WingPortWidth/2"))

    if X_LE_Tail is not None:
        derived.append(("fixed.x_LE_tail", X_LE_Tail, "m",
                         "X_LE_Tail from Fuselage measurement"))

    x_nose_gear = lookup_meas(measurements, "x_nose_gear")
    x_main_gear = lookup_meas(measurements, "x_main_gear")
    if x_nose_gear is not None:
        derived.append(("fixed.x_nose_gear", x_nose_gear, "m", "from Fuselage measurement"))
    if x_main_gear is not None:
        derived.append(("fixed.x_main_gear", x_main_gear, "m", "from Fuselage measurement"))

    derived.append(("fixed.y_main_gear", 0.419, "m", "419 mm (fixed)"))

    return derived


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        # ---- Variable Studio ----
        print("Pulling variables from Variable Studio...")
        variables = fetch_variable_studio()
        print(f"  → Found {len(variables)} variable entries")

        print_section("VARIABLE STUDIO — All Design Variables")
        print_variable_table(variables)

        # ---- Fuselage Measurements ----
        print("\nPulling measurement features from Fuselage Part Studio...")
        meas_names = fetch_measurement_features()
        print(f"  → Found {len(meas_names)} measurement features: {meas_names}")

        print("Evaluating measurements via FeatureScript...")
        measurements = evaluate_measurements(meas_names)

        print_section("FUSELAGE PART STUDIO — Evaluated Measurements (SI: Meters)")
        print_measurement_table(measurements)

        # ---- Mass Properties ----
        print_section("MASS PROPERTIES — Assembly Components")
        if UPDATE_MASSES:
            print("UPDATE_MASSES = True → fetching from API (~80 calls)...")
            components = fetch_mass_properties()
        else:
            print(f"UPDATE_MASSES = False → loading from {MASS_CACHE_FILE}...")
            components = load_cached_masses()

        # Print component summary
        total_mass = sum(c["mass"] for c in components)
        print(f"\n  {'Component':<40} {'Mass (kg)':>10} {'CG X (m)':>10} {'CG Z (m)':>10}")
        print(f"  {'-'*40} {'-'*10} {'-'*10} {'-'*10}")
        for c in components:
            marker = " ★" if is_fuel_component(c["name"]) else ""
            print(f"  {c['name'] + marker:<40} {c['mass']:>10.4f} {c['cg_x']:>10.5f} {c['cg_z']:>10.5f}")
        print(f"  {'TOTAL':<40} {total_mass:>10.4f}")
        print(f"\n  ★ = fuel component")

        # Compute CG scenarios
        cg_data = compute_cg_scenarios(components)
        print(f"\n  CG Scenarios:")
        print(f"    Both tanks full:  mass={cg_data['mass']:.4f} kg  x_cg={cg_data['x_cg_full']:.5f} m  z_cg={cg_data['z_cg_full']:.5f} m")
        print(f"    Tank 1 only:      x_cg={cg_data['x_cg_t1_only']:.5f} m")
        print(f"    Tank 2 only:      x_cg={cg_data['x_cg_t2_only']:.5f} m")
        print(f"    x_cg_min={cg_data['x_cg_min']:.5f} m  x_cg_max={cg_data['x_cg_max']:.5f} m")

        # ---- Derived Values ----
        print_section("DERIVED VALUES — All Parameters for Aerodynamics Model")
        derived = compute_derived(variables, measurements, cg_data)
        print_derived_table(derived)

        print_section("DONE")
        print()

    except Exception as e:
        print(f"\nPipeline failed: {e}")
        import traceback
        traceback.print_exc()
