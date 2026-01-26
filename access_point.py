import function
import requests
from config import Config
from re import compile
from os import makedirs, replace
import json

def refresh(id):
    function.get_token()
    url = f"{Config.dnac}/intent/api/v1/topology/physical-topology"
    header = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Auth-Token': Config.token
    }
    response = requests.get(url, headers=header, verify=False).json().get("response").get("nodes")
    ap = None
    for r in response:
        if r.get("id") == id:
            if r['label'].startswith("MY"):
                r["location"] = "Malaysia"
            elif r['label'].startswith("ID"):
                r["location"] = "Indonesia"
            elif r['label'].startswith("HK") or r['label'].startswith("MO"):
                r["location"] = "Hong Kong"
            elif r['label'].startswith("TH"):
                r["location"] = "Thailand"
            elif r["label"].startswith("PH"):
                r["location"] = "Philippines"
            elif r['label'].startswith("SG"):
                r["location"] = "Singapore"
            r["details"] = function.get_device_detail(r.get("additionalInfo").get("macAddress"))
            ap = r
            break
    return ap

def get_floor_id():
    function.get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    url = f"{Config.dnac}/intent/api/v1/site"
    response = requests.get(url, headers=header, verify=False).json().get("response")
    pattern = compile(r'\dF$')
    for r in response:
        siteName = r.get("siteNameHierarchy")
        if pattern.search(siteName):
            Config.floor_id.append(r["id"])

def fetch_ap(id):
    ap_json = None
    ind = None
    new_data = None
    with open(Config.ap_path, 'r', encoding="utf-8") as f:
        ap_json = json.load(f)
    for i, ap in enumerate(ap_json):
        if ap.get("id") == id:
            ind = i
            new_data = refresh(ap.get("id"))
            break
    ap_json[ind] = new_data
    temp = Config.ap_path + ".tmp"
    with open(temp, 'w', encoding="utf-8") as f:
        json.dump(ap_json, f, ensure_ascii=False, indent=2)
    replace(temp, Config.ap_path)
    return new_data.get("additionalInfo").get("macAddress")

def get_ap():
    function.get_token()
    access_points = []
    url = f"{Config.dnac}/intent/api/v1/topology/physical-topology"
    header = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Auth-Token': Config.token
    }
    response = requests.get(url, headers=header, verify=False).json().get("response").get("nodes")
    for r in response:
        if "Access Point" in r["deviceType"]:
            access_points.append(r)
            if r['label'].startswith("MY"):
                r["location"] = "Malaysia"
            elif r['label'].startswith("ID"):
                r["location"] = "Indonesia"
            elif r['label'].startswith("HK") or r['label'].startswith("MO"):
                r["location"] = "Hong Kong"
            elif r['label'].startswith("TH"):
                r["location"] = "Thailand"
            elif r["label"].startswith("PH"):
                r["location"] = "Philippines"
            elif r['label'].startswith("SG"):
                r["location"] = "Singapore"
            r["details"] = function.get_device_detail(r.get("additionalInfo").get("macAddress"))
    makedirs(Config.inventory_path + "/APs", exist_ok=True)
    with open(Config.ap_path, "w", encoding="utf-8") as f:
        json.dump(access_points, f, indent=4, ensure_ascii=False, default=str)

def get_Issues(device_id):
    function.get_token()
    ind = None
    data_json = None
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    
    url_inventory = f"{Config.dnac}/intent/api/v1/issues?deviceId={device_id}"
    issues = requests.get(url_inventory, headers=header, verify=False).json().get("response")
    with open(Config.ap_path, 'r', encoding="utf-8") as f:
        data_json = json.load(f)
    for i, dev in enumerate(data_json):
        if dev["id"] == device_id:
            ind = i
    data_json[ind]["issues"] = list(issues)
    tmp_path = f"{Config.ap_path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data_json, f, ensure_ascii=False, indent=2)
    replace(tmp_path, Config.ap_path )
    return issues

def get_ap_radio(ap_name, site_id):
    # print(ap_name)
    function.get_token()
    radios = None
    ind = None
    ap_json = None
    get_floor_id()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    url = f"{Config.dnac}/intent/api/v2/floors/{site_id}/accessPointPositions"
    response = requests.get(url, headers=header, verify=False).json().get("response")
    # print(response)
    for r in response:
        if r["name"] == ap_name:
            # print('true')
            radios = r["radios"]
            break
    with open(Config.ap_path, 'r', encoding="utf-8") as f:
        ap_json = json.load(f)
    for i, ap in enumerate(ap_json):
        if ap.get("label") == ap_name:
            ind = i
            break
    ap_json[ind]["radios"] = radios
    tmp_path = f"{Config.ap_path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(ap_json, f, ensure_ascii=False, indent=2)
    replace(tmp_path, Config.ap_path)
    return radios
