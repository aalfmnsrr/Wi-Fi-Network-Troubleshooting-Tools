import function
import requests
from config import Config

def get_floor_id():
    function.get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    url = f"{Config.dnac}/intent/api/v1/site"
    response = requests.get(url, headers=header, verify=False).json().get("response")
    for r in response:
        if "PFCC Tower 4-5/10F" in r["siteNameHierarchy"]:
            Config.floor10id = r["id"]
        elif "PFCC Tower 4-5/13AF" in r["siteNameHierarchy"]:
            Config.floor13aid = r["id"]

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

def get_ap_radio(ap_name):
    function.get_token()
    get_floor_id()
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