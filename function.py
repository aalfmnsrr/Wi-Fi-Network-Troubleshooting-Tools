
import requests
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from config import Config

def get_ap_radio(ap_name):
    get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    if '10F' in ap_name:
        url = f"{Config.dnac}/intent/api/v2/floors/{Config.floor10id}/accessPointPositions"
    else:
        url = f"{Config.dnac}/intent/api/v2/floors/{Config.floor13aid}/accessPointPositions"
    response = requests.get(url, headers=header, verify=False).json().get("response")
    for r in response:
        if r["name"] == ap_name:
            return r["radios"]

def get_ap():
    get_token()
    access_points = []
    url = f"{Config.dnac}/intent/api/v1/topology/physical-topology"
    header = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Auth-Token': Config.token
    }
    response = requests.get(url, headers=header, verify=False).json().get("response").get("nodes")
    for r in response:
        if "MY-PCH-10F-AP" in r["label"] or "MY-PCH-13AF-AP" in r["label"]:
            access_points.append(r)
    # print(len(access_points))
    ind = 0
    while ind < len(access_points) - 1:
        current_ap = access_points[ind]
        next_ap = access_points[ind+1]
        if current_ap == next_ap:
            access_points.remove(next_ap)
        ind += 1
    return access_points

def get_dev_details(dev_id):
    get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    url = f"{Config.dnac}/intent/api/v1/network-device/{dev_id}"
    response = requests.get(url, headers=header, verify=False)
    device = response.json().get("response")
    return device

def get_devName(dev_id):
    get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    url = f"{Config.dnac}/intent/api/v1/network-device?id={dev_id}"
    response = requests.get(url, headers=header, verify=False)
    devName = response.json().get("response")[0].get("hostname")
    return devName

def get_ap_detail(ap_mac):
    get_token()
    url = f"{Config.dnac}/intent/api/v1/device-detail?identifier=macAddress&searchBy={ap_mac}" 
    header = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Auth-Token': Config.token
    }
    ap = requests.get(url, headers=header, verify=False).json().get("response")
    return ap

def get_token():
    disable_warnings(InsecureRequestWarning)
    auth_url = f"{Config.dnac}/system/api/v1/auth/token"
    header = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    # get token
    response = requests.post(auth_url, auth=(Config.username,Config.password), headers=header, verify=False)
    Config.token = response.json().get("Token")
    # print(token)
    # return token

def get_client_enrichment_detail(client_mac):
    get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'entity_type': 'mac_address',
            'entity_value': client_mac,
            'X-Auth-Token': Config.token
    }
    url = f'{Config.dnac}/intent/api/v2/client-enrichment-details'
    client_response = requests.get(url, headers=header, verify=False)
    client = client_response.json()[0]
    # print(client)
    return client

# get clients of an AP
def get_clients():
    get_token()
    clients = []
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
    }
    url = f'{Config.dnac}/data/api/v1/clients'
    clients_response = requests.get(url, headers=header, verify=False).json()
    client = clients_response["response"]
    for c in client:
        connectedDevice = c.get('connectedNetworkDevice', {})
        if "MY-PCH-10F-AP" in connectedDevice.get('connectedNetworkDeviceName') or "MY-PCH-13AF-AP" in connectedDevice.get('connectedNetworkDeviceName'):
            clients.append(c)
    # print(len(Config.clients))
    return clients

def get_devices(): # network devices
    get_token()
    devices = []
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    url_inventory = f"{Config.dnac}/intent/api/v1/network-device"
    response = requests.get(url_inventory, headers=header, verify=False)
    devices = response.json().get("response", [])
    return devices
    # print(response.text)

# Alif Switches Devices
def get_switches(role = None): # switches devices
    get_token()
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
    Config.devices = response.json().get("response", [])
    

def get_switch_details(device_id):
    get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    url_inventory = f"{Config.dnac}/intent/api/v1/network-device?id={device_id}"
    response = requests.get(url_inventory, headers = header, verify=False).json().get("response")
    response = response[0]

    return response

def get_switch_health(device_mac):
    get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    
    url_inventory = f"{Config.dnac}/intent/api/v1/device-detail?identifier=macAddress&searchBy={device_mac}"
   
    try:
        response = requests.get(url_inventory, headers = header, verify=False, timeout=10)
    
    except requests.RequestException as e:
        raise RuntimeError(f"DNAC request failed: {e}")

    if response.status_code != 200:
        try:
            err_body = response.json()
        except Exception:
            err_body = response.text
        raise RuntimeError(f"DNAC returned {response.status_code}: {err_body}")
    
    try:
        body = response.json()
    except ValueError:
        raise RuntimeError("DNAC returned non-JSON response")
    
    data = body.get("response")
    return data

def get_vlan(device_id):
    get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    
    url_inventory = f"{Config.dnac}/intent/api/v1/network-device/{device_id}/vlan"

    try:
        response = requests.get(url_inventory, headers = header, verify=False, timeout=10)
    
    except requests.RequestException as e:
        raise RuntimeError(f"DNAC request failed: {e}")

    if response.status_code != 200:
        try:
            err_body = response.json()
        except Exception:
            err_body = response.text
        raise RuntimeError(f"DNAC returned {response.status_code}: {err_body}")

    try:
        body = response.json()
    except ValueError:
        raise RuntimeError("DNAC returned non-JSON response")
    
    vlan = body.get("response")
    return vlan