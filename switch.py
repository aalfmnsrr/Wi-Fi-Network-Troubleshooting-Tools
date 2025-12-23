# switch.py
import requests, function, access_point
from config import Config
from collections import defaultdict

# Alif Switches Devices
def get_switches(role = None): # switches devices
    function.get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    url_inventory = f"{Config.dnac}/intent/api/v1/network-device?family=Switches and Hubs"
    params = {}
    if role:
        params['role'] = role

    response = requests.get(url_inventory, headers = header, params = params, verify=False)
    devices = []
    devices = response.json().get("response", [])
    return devices

def _is_ap_node(node: dict) -> bool:
    """
    Decide if a topology node is an AP using reliable fields first (family/type),
    and fall back to name pattern.
    """
    family = (node.get("family") or "").lower()
    node_type = (node.get("deviceType") or node.get("nodeType") or "").lower()
    label = (node.get("label") or "").upper()

    # Prefer DNA Center normalized fields
    if "ap" in family or "access point" in family or "unified ap" in family:
        return True
    if "ap" in node_type:
        return True

    # Fallback: name convention
    # Adjust to your naming e.g., MY-PCH-10F-AP01, MY-PCH-13AF-AP02, etc.
    if "-AP" in label:
        return True

    return False


def get_ap_neighbors(switch_device_id):
    """
    Return a list of AP node dicts directly connected to the given switch device_id.
    Uses the physical topology: nodes + links.
    """
    function.get_token()
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Auth-Token': Config.token
    }

    url = f"{Config.dnac}/intent/api/v1/topology/physical-topology"
    topo = requests.get(url, headers=headers, verify=False).json().get("response", {})
    nodes = topo.get("nodes", []) or []
    links = topo.get("links", []) or []

    # Build an index of nodes by id
    node_by_id = {n.get("id"): n for n in nodes if n.get("id")}

    # DNA Center's node id for devices should match the network-device id
    if switch_device_id not in node_by_id:
        # Some tenants use 'physicalTopology' nodes with different id fields.
        # Try to find by 'deviceId' field if present, as a fallback.
        fallback = next((n for n in nodes if n.get("deviceId") == switch_device_id), None)
        if fallback:
            switch_node_id = fallback.get("id")
        else:
            # Try match by label/hostname as a last resort
            dev = function.get_device(switch_device_id) or {}
            hostname = (dev.get("hostname") or dev.get("name") or "").upper()
            match = next((n for n in nodes if (n.get("label") or "").upper() == hostname), None)
            if match:
                switch_node_id = match.get("id")
            else:
                # Return empty to avoid 500; you can log for troubleshooting
                return []
    else:
        switch_node_id = switch_device_id

    # Collect direct neighbor node IDs from links touching the switch node
    neighbor_ids = set()
    for lk in links:
        src = lk.get("source")
        tgt = lk.get("target")
        if src == switch_node_id and tgt:
            neighbor_ids.add(tgt)
        elif tgt == switch_node_id and src:
            neighbor_ids.add(src)

    # Filter only AP nodes
    ap_neighbors = []
    for nid in neighbor_ids:
        node = node_by_id.get(nid)
        if not node:
            continue
        if _is_ap_node(node):
            ap_neighbors.append(node)

    # Optional: de-duplicate by label
    seen = set()
    deduped = []
    for n in ap_neighbors:
        label = n.get("label")
        if label in seen:
            continue
        seen.add(label)
        deduped.append(n)

    return deduped


# switch.py (optional helpers)

def parse_ap_name(ap_label: str):
    parts = (ap_label or "").split('-')
    if len(parts) >= 4:
        return {
            "country": parts[0],
            "site": parts[1],
            "floor": parts[2],
            "device": parts[3],
        }
    return {"country": None, "site": None, "floor": None, "device": ap_label}

def group_ap_labels_by_floor(ap_nodes):
    groups = {}
    for n in ap_nodes:
        label = n.get("label", "")
        info = parse_ap_name(label)
        floor = info["floor"] or "UNKNOWN"
        groups.setdefault(floor, []).append(label)
    return groups


# def get_switch_details(device_id):
#     function.get_token()
#     header = {
#             'Content-Type': 'application/json',
#             'Accept': 'application/json',
#             'X-Auth-Token': Config.token
#         }
#     url_inventory = f"{Config.dnac}/intent/api/v1/network-device?id={device_id}"
#     response = requests.get(url_inventory, headers = header, verify=False).json().get("response")
#     response = response[0]

#     return response

# def get_switch_health(device_mac):
#     function.get_token()
#     header = {
#             'Content-Type': 'application/json',
#             'Accept': 'application/json',
#             'X-Auth-Token': Config.token
#         }
    
#     url_inventory = f"{Config.dnac}/intent/api/v1/device-detail?identifier=macAddress&searchBy={device_mac}"
   
#     data = requests.get(url_inventory, headers=header, verify=False).json().get("response")
#     return data

def get_vlan(device_id):
    function.get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    
    url_inventory = f"{Config.dnac}/intent/api/v1/network-device/{device_id}/vlan"

    vlan = requests.get(url_inventory, headers=header, verify=False).json().get("response")
    return vlan