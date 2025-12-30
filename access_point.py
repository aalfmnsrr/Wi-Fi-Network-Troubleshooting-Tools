import function
import requests
from config import Config
from re import compile

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
            elif r['label'].startswith("HK"):
                r["location"] = "Hong Kong"
            elif r['label'].startswith("TH"):
                r["location"] = "Thailand"
            elif r["label"].startswith("PH"):
                r["location"] = "Philippines"
            elif r['label'].startswith("SG"):
                r["location"] = "Singapore"
            elif r['label'].startswith("MO"):
                r["location"] = "Macao"
    # print(len(access_points))
    ind = 0
    while ind < len(access_points) - 1:
        current_ap = access_points[ind]
        next_ap = access_points[ind+1]
        if current_ap == next_ap:
            access_points.remove(next_ap)
        ind += 1
    return access_points

def get_ap_radio(ap_name, site_id):
    # print(ap_name)
    function.get_token()
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
        # print(r)
        if r["name"] == ap_name:
            # print('true')
            return r["radios"]