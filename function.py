import requests, json
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from config import Config
from datetime import datetime, timedelta
from netmiko import ConnectHandler
from os import replace

def get_date(*input):
    if len(input) != 0:
        date = datetime.now() - timedelta(days=input[0])
    else:
        # define variable
        date = datetime.now()
    year = date.strftime("%Y")
    month = date.strftime("%m")
    day = date.strftime("%d")
    time = date.strftime("%H.%M")
    return {"year": year, "month": month, "day": day, "time": time}

def append_file(filename, output):
    try:
        if not filename:
            file = open(filename, "w")
        file = open(filename, "a")
        file.writelines(output)
        file.close()
        return "File Successfully saved."
    except FileNotFoundError as error:
        return str(error)
    
# append new details info if details is null
def append_details(mac, type):
    ind = None
    path = ""
    mac_in_file = ""
    if type == "AP":
        path = Config.ap_path
    elif type == "WLC":
        path = Config.wlc_path
    elif type == "Switch":
        path = Config.switch_path
    with open(path, 'r', encoding="utf-8") as f:
        data_json = json.load(f)    
    for i, item in enumerate(data_json):
        if type == "AP":
            mac_in_file = item.get("additionalInfo").get("macAddress").upper()  
        elif type == "WLC":
            mac_in_file = item.get("macAddress").upper()
        elif type == "Switch":
            mac_in_file = item.get("macAddress").upper()
        if mac_in_file == mac.upper():
            ind = i
            break
    details = get_device_detail(mac)
    data_json[ind]["details"] = dict(details)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data_json, f, ensure_ascii=False, indent=2)
    replace(tmp_path, path)
    return details

def append_AP_dev(dev_id, type):
    ind = None
    path = ""
    id_in_file = ""
    data_json = None
    if type == "AP":
        path = Config.ap_path
    elif type == "WLC":
        path = Config.wlc_path
    elif type == "Switch":
        path = Config.switch_path
    with open(path, 'r', encoding="utf-8") as f:
        data_json = json.load(f)    
    for i, item in enumerate(data_json):
        id_in_file = item.get("id") 
        if id_in_file == dev_id:
            ind = i
            break
    get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    url = f"{Config.dnac}/intent/api/v1/network-device/{dev_id}"
    response = requests.get(url, headers=header, verify=False)
    device = response.json().get("response")
    data_json[ind]["device"] = dict(device)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data_json, f, ensure_ascii=False, indent=2)
    replace(tmp_path, path)
    return device
    
def get_dc(wlc_id):
    with open(Config.wlc_path, "r", encoding="utf-8") as f:
        wlc_json = json.load(f)
        for wlc in wlc_json:
            if wlc.get("id") == wlc_id:
                if wlc.get("dc") == "Thailand":
                    return "TH-NTT"
                elif wlc.get("dc") == "Singapore":
                    return "APDC"
                elif wlc.get("dc") == "Hong Kong":
                    return "HK-NTT"
                elif wlc.get("dc") == "Indonesia":
                    return "INDO"

def get_cdp(device):
    device = {
        "device_type": "cisco_ios",  
        "host": device.get(""),
        "username": Config.cisco_user,
        "password": Config.cisco_pass,
        "secret": Config.cisco_pass, 
    }
    with ConnectHandler(**device) as net_connect:
        command_output = net_connect.send_command(
                        "show cdp neighbors",
                        read_timeout=600,
                        )   
        print(command_output)
    # return command_output
    
def get_site_id(location):
    get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    url = f"{Config.dnac}/intent/api/v1/site"
    response = requests.get(url, headers=header, verify=False).json().get("response")
    # print(response)
    for r in response:
        if r["siteNameHierarchy"] == location:
            # print(r.get("id"))
            return r.get("id")

def get_device(dev_id, type):
    if type == "AP":
        path = Config.ap_path 
    elif type == "WLC":
        path = Config.wlc_path 
    elif type == "Switch":
        path = Config.switch_path 
    with open(path, 'r', encoding="utf-8") as f:
        device_json = json.load(f)
        for d in device_json:
            if d["id"] == dev_id:
                return d

def get_devName(dev_id, devType):
    if devType == "AP":
        with open(Config.ap_path, 'r', encoding="utf-8") as f:
            ap_json = json.load(f)
        for ap in ap_json:
            if ap.get("id") == dev_id:
                return ap.get("label")
    elif devType == "WLC":
        with open(Config.wlc_path, 'r', encoding="utf-8") as f:
            wlc_json = json.load(f)
        for wlc in wlc_json:
            if wlc.get("id") == dev_id:
                return wlc.get("label")
    elif devType == "Switch":
        with open(Config.switch_path, 'r', encoding="utf-8") as f:
            sw_json = json.load(f)
        for sw in sw_json:
            if sw.get("id") == dev_id:
                return sw.get("label")

def get_device_detail(mac):
    get_token()
    url = f"{Config.dnac}/intent/api/v1/device-detail?identifier=macAddress&searchBy={mac}" 
    header = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Auth-Token': Config.token
    }
    details = requests.get(url, headers=header, verify=False).json().get("response")
    return details

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

def get_reach(mac):
    get_token()
    header = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Auth-Token': Config.token
    }
    url = f"{Config.dnac}/intent/api/v1/device-detail?identifier=macAddress&searchBy={mac}"
    response = requests.get(url, headers=header, verify=False).json().get("response").get("overallHealth")
    return response