import requests
from requests.auth import HTTPBasicAuth
import csv
import os

# ==========================================
# 1. Credentials & Target Assembly
# ==========================================
ACCESS_KEY = 'on_jsbnmgzkR9IhNJP5epMsG'
SECRET_KEY = 'Y9yIoS8lTX8XJLIlL13O43FsZPPm1HZo10LrqhxjoK4ZHoxg'

DOCUMENT_ID = "e17cbed2e815359ba964f636"
WORKSPACE_ID = "93d2dfcb61f932badc048181"
ELEMENT_ID = "1f24790f90e799bbc1eb8f34"

BASE_URL = "https://cad.onshape.com/api/v10"
CSV_FILENAME = "onshape_mass_distribution.csv"

# ==========================================
# 2. Helper Functions
# ==========================================
def get_onshape_data(url, params=None):
    """Handles the API GET request with authentication and parameters."""
    headers = {
        'Accept': 'application/vnd.onshape.v1+json',
        'Content-Type': 'application/json'
    }
    response = requests.get(
        url,
        auth=HTTPBasicAuth(ACCESS_KEY, SECRET_KEY),
        headers=headers,
        params=params
    )
    if response.status_code != 200:
        return None
    return response.json()

def extract_vertices(node, vertices_list):
    """Recursively hunts down 'vertices' arrays and forces them into a flat float list."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == 'vertices' and isinstance(v, list):
                for item in v:
                    # Case 1: Nested lists [[x, y, z], [x, y, z]]
                    if isinstance(item, list) and len(item) >= 3:
                        vertices_list.extend([float(item[0]), float(item[1]), float(item[2])])
                    # Case 2: Flat array [x1, y1, z1, x2, y2, z2]
                    elif isinstance(item, (int, float)):
                        vertices_list.append(float(item))
                    # Case 3: Dictionaries [{'x': 0.0, 'y': 0.0, 'z': 0.0}]
                    elif isinstance(item, dict):
                        if 'x' in item and 'y' in item and 'z' in item:
                            vertices_list.extend([float(item['x']), float(item['y']), float(item['z'])])
                        else:
                            # Fallback for unknown dict structures, grab first 3 values
                            vals = list(item.values())
                            if len(vals) >= 3:
                                vertices_list.extend([float(vals[0]), float(vals[1]), float(vals[2])])
            else:
                extract_vertices(v, vertices_list)
    elif isinstance(node, list):
        for item in node:
            extract_vertices(item, vertices_list)

# ==========================================
# 3. Main Execution
# ==========================================
def main():
    print("Fetching Assembly Definition and transforming coordinates...")
    
    assembly_url = f"{BASE_URL}/assemblies/d/{DOCUMENT_ID}/w/{WORKSPACE_ID}/e/{ELEMENT_ID}"
    assembly_data = get_onshape_data(assembly_url)
    
    if not assembly_data:
        print("Failed to retrieve assembly data. Check your IDs and API Keys.")
        return

    instances_dict = {}
    
    if 'rootAssembly' in assembly_data:
        for inst in assembly_data['rootAssembly'].get('instances', []):
            instances_dict[inst['id']] = inst
            
    for sub in assembly_data.get('subAssemblies', []):
        for inst in sub.get('instances', []):
            instances_dict[inst['id']] = inst

    part_cache = {}
    occurrences = assembly_data.get('rootAssembly', {}).get('occurrences', [])
    
    print(f"Found {len(occurrences)} occurrence(s). Processing and streaming to CSV...\n")
    print("-" * 50)
    
    with open(CSV_FILENAME, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        
        writer.writerow([
            "Component Name", 
            "Mass (kg)", 
            "Size X (m)", "Size Y (m)", "Size Z (m)", 
            "Assembly CG X (m)", "Assembly CG Y (m)", "Assembly CG Z (m)"
        ])
        
        for occ in occurrences:
            path = occ.get('path', [])
            if not path:
                continue
                
            inst_id = path[-1]
            inst = instances_dict.get(inst_id)
            
            if not inst or inst.get('type') != 'Part':
                continue
                
            name = inst.get('name', 'Unknown Part')
            part_id = inst.get('partId')
            doc_id = inst.get('documentId')
            elem_id = inst.get('elementId')
            m_id = inst.get('documentMicroversion')
            config = inst.get('configuration', '')
            
            transform = occ.get('transform', [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])
            cache_key = f"{doc_id}_{elem_id}_{part_id}_{config}"
            
            if cache_key not in part_cache:
                wvm = 'm' if m_id else 'w'
                wvmid = m_id if m_id else WORKSPACE_ID
                
                # Initialize the params dictionary robustly
                params = {'configuration': config} if config else {}
                
                # FORCE the API to respect manual UI overrides
                params['useMassPropertyOverrides'] = 'true'
                
                # Fetch Mass Properties
                mass_url = f"{BASE_URL}/parts/d/{doc_id}/{wvm}/{wvmid}/e/{elem_id}/partid/{part_id}/massproperties"
                mass_data = get_onshape_data(mass_url, params)
                
                mass = 0.0
                cx, cy, cz = 0.0, 0.0, 0.0
                if mass_data and 'bodies' in mass_data:
                    body_data = mass_data['bodies'].get(part_id, {})
                    mass = body_data.get('mass', [0.0])[0]
                    centroid = body_data.get('centroid', [0.0, 0.0, 0.0])
                    if len(centroid) >= 3:
                        cx, cy, cz = centroid[0], centroid[1], centroid[2]

                # ----------------------------------------------------
                # EXACT BOUNDS ROUTE: Tessellated Faces
                # ----------------------------------------------------
                tess_url = f"{BASE_URL}/parts/d/{doc_id}/{wvm}/{wvmid}/e/{elem_id}/partid/{part_id}/tessellatedfaces"
                tess_data = get_onshape_data(tess_url, params)
                
                size_x, size_y, size_z = 0.0, 0.0, 0.0
                
                if tess_data:
                    vertices = []
                    extract_vertices(tess_data, vertices)
                    
                    if len(vertices) >= 3:
                        xs = vertices[0::3]
                        ys = vertices[1::3]
                        zs = vertices[2::3]
                        
                        size_x = max(xs) - min(xs)
                        size_y = max(ys) - min(ys)
                        size_z = max(zs) - min(zs)
                
                # ----------------------------------------------------
                # HYBRID FALLBACK: Standard Bounding Box
                # ----------------------------------------------------
                if size_x == 0.0 and size_y == 0.0 and size_z == 0.0:
                    bbox_url = f"{BASE_URL}/parts/d/{doc_id}/{wvm}/{wvmid}/e/{elem_id}/partid/{part_id}/boundingboxes"
                    bbox_data = get_onshape_data(bbox_url, params)
                    if bbox_data:
                        box = bbox_data if 'lowX' in bbox_data else bbox_data.get('bodies', {}).get(part_id, {})
                        if 'lowX' in box and 'highX' in box:
                            size_x = box['highX'] - box['lowX']
                            size_y = box['highY'] - box['lowY']
                            size_z = box['highZ'] - box['lowZ']
                
                # Store in cache
                part_cache[cache_key] = {
                    'mass': mass,
                    'cx': cx, 'cy': cy, 'cz': cz,
                    'sx': size_x, 'sy': size_y, 'sz': size_z
                }
                
            props = part_cache[cache_key]
            
            tx, ty, tz = transform[3], transform[7], transform[11]
            cg_x = (transform[0] * props['cx']) + (transform[1] * props['cy']) + (transform[2] * props['cz']) + tx
            cg_y = (transform[4] * props['cx']) + (transform[5] * props['cy']) + (transform[6] * props['cz']) + ty
            cg_z = (transform[8] * props['cx']) + (transform[9] * props['cy']) + (transform[10] * props['cz']) + tz
            
            print(f"Exporting: {name}")
            
            writer.writerow([
                name,
                round(props['mass'], 5),
                round(props['sx'], 5), round(props['sy'], 5), round(props['sz'], 5),
                round(cg_x, 5), round(cg_y, 5), round(cg_z, 5)
            ])

    print("-" * 50)
    print(f"SUCCESS: Data successfully exported to {os.path.abspath(CSV_FILENAME)}")

if __name__ == "__main__":
    main()