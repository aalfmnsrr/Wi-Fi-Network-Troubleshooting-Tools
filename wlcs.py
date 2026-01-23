import function
import requests
from config import Config
from os import makedirs, replace
import json

def refresh(id):
    function.get_token()
    new_data = None
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    url_inventory = f"{Config.dnac}/intent/api/v1/network-device?family=Wireless Controller"
    response = requests.get(url_inventory, headers=header, verify=False)
    wlc = response.json().get("response", [])
    for w in wlc:
        if w.get("id") == id:
            if 'HK-NTT' in w.get('hostname'):
                w['dc'] = 'Hong Kong'
            elif 'TH-NTT' in w.get('hostname'):
                w['dc'] = 'Thailand'
            elif 'INDO' in w.get('hostname'):
                w['dc'] = 'Indonesia'
            elif 'APDC' in w.get('hostname'):
                w['dc'] = 'Singapore'
            details = function.get_device_detail(w.get("macAddress"))
            w["details"] = details
            w["ssid"] = get_ssid(w.get("id"))
            w["interface"] = wlc_int(w.get("id"))
            w["physical"] = get_physical(w.get("id"))
            w["AP"] = get_AP_in_WLC(w.get("managementIpAddress"))
            site = details.get('siteHierarchyGraphId').strip("/").split("/")[-1]
            w["health"] = health(site, w.get("id"))
            new_data = w
            break
    return new_data

def fetch_wlc(id):
    wlc_json = None
    ind = None
    new_data = None
    with open(Config.wlc_path, 'r', encoding="utf-8") as f:
        wlc_json = json.load(f)
    for i, wlc in enumerate(wlc_json):
        if wlc.get("id") == id:
            ind = i
            new_data = refresh(wlc.get("id"))
            break
    wlc_json[ind] = new_data
    temp = Config.wlc_path + ".tmp"
    with open(temp, 'w', encoding="utf-8") as f:
        json.dump(wlc_json, f, ensure_ascii=False, indent=2)
    replace(temp, Config.wlc_path)

def get_wlc(): #get wlc
    function.get_token()

    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    url_inventory = f"{Config.dnac}/intent/api/v1/network-device?family=Wireless Controller"
    response = requests.get(url_inventory, headers=header, verify=False)
    wlc = response.json().get("response", [])
    for w in wlc:
        if 'HK-NTT' in w.get('hostname'):
            w['dc'] = 'Hong Kong'
        elif 'TH-NTT' in w.get('hostname'):
            w['dc'] = 'Thailand'
        elif 'INDO' in w.get('hostname'):
            w['dc'] = 'Indonesia'
        elif 'APDC' in w.get('hostname'):
            w['dc'] = 'Singapore'
        details = function.get_device_detail(w.get("macAddress"))
        w["details"] = details
        w["ssid"] = get_ssid(w.get("id"))
        w["interface"] = wlc_int(w.get("id"))
        w["physical"] = get_physical(w.get("id"))
        w["AP"] = get_AP_in_WLC(w.get("managementIpAddress"))
        site = details.get('siteHierarchyGraphId').strip("/").split("/")[-1]
        w["health"] = health(site, w.get("id"))
    makedirs(Config.inventory_path + "/WLCs", exist_ok=True)
    with open(f"{Config.wlc_path}/wlc.json", "w", encoding="utf-8") as f:
        json.dump(wlc, f, indent=4, ensure_ascii=False, default=str)

def get_wlc_by_id(wlc_id): #same as above but to avoid long time reloading
    wlc = []
    function.get_token()

    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    url_inventory = f"{Config.dnac}/data/api/v1/networkDevices/{wlc_id}"
    response = requests.get(url_inventory, headers=header, verify=False)
    wlc = response.json().get("response", [])
    makedirs(Config.wlc_path, exist_ok=True)
    with open(f"{Config.wlc_path}/wlc.json", "w", encoding="utf-8") as f:
        json.dump(wlc, f, indent=4, ensure_ascii=False, default=str)

def wlc_id(wlc_ip):

    function.get_token()
    url_inventory = f"https://{Config.dnac}/api/v1/network-device/ip-address/{wlc_ip}"
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    response = requests.get(url_inventory, headers=header, verify=False)

    # print(json.dumps(response.json(), indent=2))

    wlc_id = response.json().get('response').get('id')
    return wlc_id

def wlc_int(wlc_id):

    function.get_token()
    url_inventory = f"https://{Config.dnac}/api/v1/interface/network-device/{wlc_id}"

    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }

    response = requests.get(url_inventory, headers=header, verify=False)

    response = response.json().get('response')

    return response

# print(wlc_int('baa57c39-1a79-41df-9f56-4bbadd26d84f'))

def get_ssid(wlc_id):

    function.get_token()
    url_inventory = f'{Config.dnac}/intent/api/v1/wirelessControllers/{wlc_id}/ssidDetails'

    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    response = requests.get(url_inventory, headers=header, verify=False)

    response = response.json().get('response')

    return response

def get_physical(wlc_id):

    function.get_token()
    url_inventory = f'{Config.dnac}/intent/api/v1/network-device/{wlc_id}/equipment'

    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    response = requests.get(url_inventory, headers=header, verify=False)

    response = response.json().get('response')

    return response


def get_AP_in_WLC(wlc_ip):

    function.get_token()
    i = 0
    ap_wlc = []  

    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }

    url_wlc = f'{Config.dnac}/intent/api/v1/network-device?associatedWlcIp={wlc_ip}'
    response = requests.get(url_wlc, headers=header, verify=False).json().get('response')

    for r in response:
        if "MY-PCH-" in r["hostname"]:
            ap_wlc.append(r)
            ap_wlc[-1]["office"] = "MY"
        elif "PH-GTT" in r["hostname"]:
            ap_wlc.append(r)
            ap_wlc[-1]["office"] = "PH"
        elif "SG-CPG-" in r["hostname"]:
            ap_wlc.append(r)
            ap_wlc[-1]["office"] = "SG"
        else:
            ap_wlc.append(r)
                
    return ap_wlc

def health(site_id, wlc_id):
    #note that both AP wlc has the same site id
    function.get_token()

    url_health = f"{Config.dnac}/intent/api/v1/device-health?siteId={site_id}" 

    header = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Auth-Token': Config.token
    }
        
    response = requests.get(url_health, headers = header, verify = False).json().get('response')
    #one site id contains both wlc or other things

    health = []

    for r in response:
        if wlc_id == r.get('uuid'):
            health = r

    return health

def health_wlc(dc, wlc_ip):
    #note that both AP wlc has the same site id
    function.get_token()
   

    url = f"{Config.dnac}/intent/api/v1/topology/physical-topology"
    header = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Auth-Token': Config.token
    }

    health = []

    response = requests.get(url, headers = header, verify = False).json().get('response').get('nodes')

    for r in response:
        if dc in r["label"]:
            siteIdWlc = r["additionalInfo"]["siteid"]
    # else:
        # print('no site')
    # print(siteId)
    url_health = f"{Config.dnac}/intent/api/v1/device-health?siteId={siteIdWlc}" 
        
    response_health = requests.get(url_health, headers = header, verify = False).json().get('response')
    #one site id contains both wlc or other things

    for r in response_health:
        if r.get("deviceFamily") == "WIRELESS_CONTROLLER":
            health.append(r)

    return health

def wlc_int(wlc_id):
    function.get_token()

    url = f"{Config.dnac}/intent/api/v1/interface/network-device/{wlc_id}"
    header = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Auth-Token': Config.token
    } 

    response = requests.get(url, headers = header, verify = False).json().get('response')

    return response