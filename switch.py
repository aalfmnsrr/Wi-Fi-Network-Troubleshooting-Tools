# switch.py
import requests, function, access_point
from config import Config
from collections import defaultdict

# Retrieving switches based on their role
def get_switches(role = None): # get switch by role
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

# Retrieving location of the switches
def _extract_clean_location(raw: str) -> str | None:
    """
    Robust cleaner to turn 'AXA GO Hong Kong' or 'AXA GO Operations Hong Kong'
    into 'Hong Kong'. Adjust patterns as needed.
    """
    if not raw:
        return None

    loc = raw.strip()

    # If some locations have an 'Operations' section before the actual city
    # e.g., 'Something Operations Hong Kong' -> take the right-hand side.
    # We do this first so that the 'AXA GO' prefix removal still works even if it's repeated.
    parts = re.split(r'\bOperations\b', loc, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) == 2:
        loc = parts[1].strip()

    # Remove known org prefix like 'AXA GO' at the beginning (case-insensitive, extra spaces ok)
    loc = re.sub(r'^\s*AXA\s*GO\s*', '', loc, flags=re.IGNORECASE).strip()

    # If you only want the **last token** (e.g., 'Hong Kong' stays as 'Hong Kong' because it's two words),
    # we keep as-is. If sometimes you get 'Hong Kong Building 12', consider more rules here.

    return loc or None

def get_swLocation():
    function.get_token()
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Auth-Token': Config.token
    }
    url_inventory = f"{Config.dnac}/intent/api/v1/network-device?family=Switches and Hubs"

    resp = requests.get(url_inventory, headers=headers, verify=False)
    resp.raise_for_status()
    response_list = resp.json().get("response", [])

    sw_location = {}
    for dev in response_list:
        dev_id = dev.get('id')
        raw = dev.get('snmpLocation')
        clean = _extract_clean_location(raw)
        if dev_id:
            sw_location[dev_id] = clean

    return sw_location

# Retrieving AP that connected to the switch
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

# Retriving VLAN information
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

# Retrieving interfaces from the switch
def get_interface(device_id):
    function.get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    
    url_inventory = f"{Config.dnac}/data/api/v1/interfaces?networkDeviceId={device_id}"
   
    interfaces = requests.get(url_inventory, headers=header, verify=False).json().get("response")
    return interfaces

# Converting interface speed 
def format_speed_kbps(value):
    """
    Convert numeric speed from Kbps to a human-friendly string:
    - 1,000,000 Kbps => 1.00 Gbps
    - 100,000 Kbps   => 100 Mbps
    - 500 Kbps       => 500 Kbps
    Handles None/empty gracefully.
    """
    if value is None:
        return '-'
    try:
        s = str(value).strip()
        if not s:
            return '-'
        n = int(s)  # n is Kbps (as per DNAC)
    except Exception:
        # Non-numeric strings pass through
        return str(value)

    if n >= 1_000_000:
        return f"{n / 1_000_000:.0f} Gbps"
    elif n >= 1_000:
        return f"{n / 1_000:.0f} Mbps"
    else:
        return f"{n} Kbps"

# Retrieving stacking switch information (stack/svl)
def get_stack_info(device_id):
    function.get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    
    url_inventory = f"{Config.dnac}/intent/api/v1/network-device/{device_id}/stack"
   
    stack = requests.get(url_inventory, headers=header, verify=False).json().get("response")
    return stack

def _parse_member_from_stack_port(port_str):
    """StackWise style 'X/Y' -> member int X."""
    if not port_str or '/' not in port_str:
        return None
    try:
        member_str, _ = port_str.split('/', 1)
        return int(member_str)
    except Exception:
        return None

def _parse_member_from_interface_name(if_name):
    """
    SVL interface style 'TenGigabitEthernet2/0/5' -> member int 2.
    Works with common Catalyst names (GigabitEthernet, TenGigabitEthernet, etc.).
    """
    if not if_name:
        return None
    # Try to find digits right after the interface family
    m = re.search(r'(?:[A-Za-z]*GigabitEthernet|HundredGigE)(\d+)', if_name)
    if m:
        return int(m.group(1))
    # Fallback: trailing digits before first slash (e.g., 'Te2/0/5' patterns)
    first = if_name.split('/', 1)[0]
    m2 = re.search(r'(\d+)$', first)
    return int(m2.group(1)) if m2 else None

def dict_stack_summary(stack):
    """
    Classic StackWise summary (one row per switch member).
    Uses stackPortInfo when available; otherwise sets '-' for neighbors.
    Returns list of dict rows:
      {
        'switch_num', 'serial', 'pID', 'mac', 'role', 'state', 'priority',
        'port1_neighbor_sw', 'port2_neighbor_sw'
      }
    """
    resp = stack or {}
    sws = resp.get('stackSwitchInfo') or []
    ports = resp.get('stackPortInfo') or []

    # Per-member metadata
    members_meta = {}
    for s in sws:
        member_num = s.get('stackMemberNumber')
        try:
            member_num = int(member_num)
        except Exception:
            continue
        members_meta[member_num] = {
            'serial': s.get('serialNumber') or '-',
            'pID': s.get('platformId') or '-',
            'mac': s.get('macAddress') or '-',
            'role': s.get('role') or '-',
            'state': s.get('state') or '-',
            'priority': s.get('switchPriority') or '-',
        }

    # Map 'X/Y' -> 'A/B'
    neighbors = {}
    for p in ports or []:
        sp = (p or {}).get('switchPort')
        np = (p or {}).get('neighborPort')
        if sp and np and '/' in sp and '/' in np:
            neighbors[sp] = np

    rows = []
    for member_num, meta in members_meta.items():
        local_p1 = f"{member_num}/1"
        local_p2 = f"{member_num}/2"
        p1_neighbor = _parse_member_from_stack_port(neighbors.get(local_p1))
        p2_neighbor = _parse_member_from_stack_port(neighbors.get(local_p2))

        rows.append({
            'switch_num': member_num,
            'serial': meta['serial'],
            'pID': meta['pID'],
            'mac': meta['mac'],
            'role': meta['role'],
            'state': meta['state'],
            'priority': meta['priority'],
            'port1_neighbor_sw': p1_neighbor if p1_neighbor is not None else '-',
            'port2_neighbor_sw': p2_neighbor if p2_neighbor is not None else '-',
        })

    rows.sort(key=lambda r: r['switch_num'])
    return rows

def dict_svl_summary(stack):
    """
    SVL summary (one row per SVL member), aggregating multiple links.
    Returns a list of dict rows:
      {
        'switch_num': 1,
        'serial': 'FCW...',
        'pID': 'C9500-16X',
        'mac': 'a4:b4:...',
        'role': 'ACTIVE',
        'state': 'READY',
        'priority': 15,
        'src_ports': ['TenGigabitEthernet1/0/5', 'TenGigabitEthernet1/0/6'],
        'dest_ports': ['TenGigabitEthernet2/0/5', 'TenGigabitEthernet2/0/6'],
        'dad': 'TenGigabitEthernet1/0/4'  # or '-' if not present
      }
    """
    resp = stack or {}
    sws = resp.get('stackSwitchInfo') or []
    svls = resp.get('svlSwitchInfo') or []

    # Per-member metadata from stackSwitchInfo (fallbacks to '-' if missing)
    members_meta = {}
    for s in sws:
        member_num = s.get('stackMemberNumber')
        try:
            member_num = int(member_num)
        except Exception:
            continue
        members_meta[member_num] = {
            'serial': s.get('serialNumber') or '-',
            'pID': s.get('platformId') or '-',
            'mac': s.get('macAddress') or '-',
            'role': s.get('role') or '-',
            'state': s.get('state') or '-',
            'priority': s.get('switchPriority') or '-',
        }

    # Helper: ordered unique
    def uniq(seq):
        seen = set()
        ordered = []
        for x in seq:
            if x and x not in seen:
                seen.add(x)
                ordered.append(x)
        return ordered

    # Aggregate rows per member
    agg = {}  # member -> row dict

    for domain in svls or []:
        switch_members = domain.get('switchMembers') or []

        # DAD per member (if enabled)
        dad_per_member = {}
        for sm in switch_members:
            local_member = sm.get('svlMemberNumber')
            try:
                local_member = int(local_member)
            except Exception:
                continue
            pep = sm.get('svlMemberPepSettings') or []
            dad_name = None
            for item in pep:
                # prefer enabled DAD interface if present
                if item.get('dadEnabled'):
                    dad_name = item.get('dadInterfaceName') or dad_name
            if dad_name:
                dad_per_member[local_member] = dad_name

        for sm in switch_members:
            local_member = sm.get('svlMemberNumber')
            try:
                local_member = int(local_member)
            except Exception:
                continue

            # Seed row with metadata (or defaults if absent in stackSwitchInfo)
            row = agg.setdefault(local_member, {
                'switch_num': local_member,
                'serial': members_meta.get(local_member, {}).get('serial', '-'),
                'pID': members_meta.get(local_member, {}).get('pID', '-'),
                'mac': members_meta.get(local_member, {}).get('mac', '-'),
                'role': members_meta.get(local_member, {}).get('role', '-'),
                'state': members_meta.get(local_member, {}).get('state', '-'),
                'priority': members_meta.get(local_member, {}).get('priority', '-'),
                'src_ports': [],
                'dest_ports': [],
                'dad': dad_per_member.get(local_member, '-'),
            })

            # Collect all endpoint links for this member
            endpoints = sm.get('svlMemberEndPoints') or []
            for ep in endpoints:
                ports_list = ep.get('svlMemberEndPointPorts') or []
                for link in ports_list:
                    src = link.get('swLocalInterface') or None
                    dst = link.get('swRemoteInterface') or None
                    if src:
                        row['src_ports'].append(src)
                    if dst:
                        row['dest_ports'].append(dst)

    # Finalize: uniq + sort rows
    rows = []
    for member, r in agg.items():
        r['src_ports'] = uniq(r['src_ports'])
        r['dest_ports'] = uniq(r['dest_ports'])
        rows.append(r)

    rows.sort(key=lambda r: r['switch_num'])
    return rows

# Retrieving POE from switch
def get_poe(device_id): 
    function.get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    
    url_inventory = f"{Config.dnac}/intent/api/v1/network-device/{device_id}/poe"
   
    poe = requests.get(url_inventory, headers=header, verify=False).json().get("response")
    return poe

def get_switchIssues(device_id):
    function.get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    
    url_inventory = f"{Config.dnac}/intent/api/v1/issues?deviceId={device_id}"
   
    issues = requests.get(url_inventory, headers=header, verify=False).json().get("response")
    return issues

# Retrieving stacking switch information (stack/svl)
def get_stack_info(device_id):
    function.get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    
    url_inventory = f"{Config.dnac}/intent/api/v1/network-device/{device_id}/stack"
   
    stack = requests.get(url_inventory, headers=header, verify=False).json().get("response")
    return stack

def dict_stack(stack):
    # this function will return list of dict of stack
    stack_dict = []
    sws = stack.get('stackSwitchInfo') or []
    ports = stack.get('stackPortInfo') or []

    neighbors = {}
    for p in ports:
        sp = p.get('switchPort') 
        np = p.get('neighborPort')     
        if sp and np and '/' in sp and '/' in np:
            neighbors[sp] = np
    
    def neighbor_member_num(port_str):
        member_str, _ = port_str.split('/', 1)
        return int(member_str)
    except Exception:
        return None

def _parse_member_from_interface_name(if_name):
    """
    SVL interface style 'TenGigabitEthernet2/0/5' -> member int 2.
    Works with common Catalyst names (GigabitEthernet, TenGigabitEthernet, etc.).
    """
    if not if_name:
        return None
    # Try to find digits right after the interface family
    m = re.search(r'(?:[A-Za-z]*GigabitEthernet|HundredGigE)(\d+)', if_name)
    if m:
        return int(m.group(1))
    # Fallback: trailing digits before first slash (e.g., 'Te2/0/5' patterns)
    first = if_name.split('/', 1)[0]
    m2 = re.search(r'(\d+)$', first)
    return int(m2.group(1)) if m2 else None


def dict_stack_summary(stack):
    """
    Classic StackWise summary (one row per switch member).
    Uses stackPortInfo when available; otherwise sets '-' for neighbors.
    Returns list of dict rows:
      {
        'switch_num', 'serial', 'pID', 'mac', 'role', 'state', 'priority',
        'port1_neighbor_sw', 'port2_neighbor_sw'
      }
    """
    resp = stack or {}
    sws = resp.get('stackSwitchInfo') or []
    ports = resp.get('stackPortInfo') or []

    # Per-member metadata
    members_meta = {}
    for s in sws:
        member_num = s.get('stackMemberNumber')
        if member_num is None:
            continue

        member_num = int(member_num)

        # Local ports: 1/1 and 1/2, 2/1 and 2/2, etc.
        local_p1 = f"{member_num}/1"
        local_p2 = f"{member_num}/2"

        # Resolve neighbor switch numbers
        p1_neighbor_sw = neighbor_member_num(neighbors.get(local_p1))
        p2_neighbor_sw = neighbor_member_num(neighbors.get(local_p2))

        stack_dict.append({
            'switch_num': member_num,
            'serial': meta['serial'],
            'pID': meta['pID'],
            'mac': meta['mac'],
            'role': meta['role'],
            'state': meta['state'],
            'priority': meta['priority'],
            'port1_neighbor_sw': p1_neighbor if p1_neighbor is not None else '-',
            'port2_neighbor_sw': p2_neighbor if p2_neighbor is not None else '-',
        })

    rows.sort(key=lambda r: r['switch_num'])
    return rows

# switch.py

def dict_svl_summary(stack):
    """
    SVL summary (one row per SVL member), aggregating multiple links.
    Returns a list of dict rows:
      {
        'switch_num': 1,
        'serial': 'FCW...',
        'pID': 'C9500-16X',
        'mac': 'a4:b4:...',
        'role': 'ACTIVE',
        'state': 'READY',
        'priority': 15,
        'src_ports': ['TenGigabitEthernet1/0/5', 'TenGigabitEthernet1/0/6'],
        'dest_ports': ['TenGigabitEthernet2/0/5', 'TenGigabitEthernet2/0/6'],
        'dad': 'TenGigabitEthernet1/0/4'  # or '-' if not present
      }
    """
    resp = stack or {}
    sws = resp.get('stackSwitchInfo') or []
    svls = resp.get('svlSwitchInfo') or []

    # Per-member metadata from stackSwitchInfo (fallbacks to '-' if missing)
    members_meta = {}
    for s in sws:
        member_num = s.get('stackMemberNumber')
        try:
            member_num = int(member_num)
        except Exception:
            continue
        members_meta[member_num] = {
            'serial': s.get('serialNumber') or '-',
            'pID': s.get('platformId') or '-',
            'mac': s.get('macAddress') or '-',
            'role': s.get('role') or '-',
            'state': s.get('state') or '-',
            'priority': s.get('switchPriority') or '-',
            # Display-friendly: convert None to '-' so Jinja shows a dash instead of blank
            'port1_neighbor_sw': p1_neighbor_sw if p1_neighbor_sw is not None else '-',
            'port2_neighbor_sw': p2_neighbor_sw if p2_neighbor_sw is not None else '-',
        })

    # Finalize: uniq + sort rows
    rows = []
    for member, r in agg.items():
        r['src_ports'] = uniq(r['src_ports'])
        r['dest_ports'] = uniq(r['dest_ports'])
        rows.append(r)

    rows.sort(key=lambda r: r['switch_num'])
    return rows



def get_poe(device_id): 
    function.get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    
    url_inventory = f"{Config.dnac}/intent/api/v1/network-device/{device_id}/poe"
   
    poe = requests.get(url_inventory, headers=header, verify=False).json().get("response")
    return poe

def get_switchIssues(device_id):
    function.get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    
    url_inventory = f"{Config.dnac}/intent/api/v1/issues?deviceId={device_id}"
   
    issues = requests.get(url_inventory, headers=header, verify=False).json().get("response")
    return issues

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