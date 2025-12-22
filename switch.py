import requests, function
from config import Config

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

def get_switch_details(device_id):
    function.get_token()
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
    function.get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    
    url_inventory = f"{Config.dnac}/intent/api/v1/device-detail?identifier=macAddress&searchBy={device_mac}"
   
    data = requests.get(url_inventory, headers=header, verify=False).json().get("response")
    return data

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