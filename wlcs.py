import function
import requests
from config import Config

def get_wlc(dc): #get wlc
    wlc = []
    function.get_token()

    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    url_inventory = f"{Config.dnac}/intent/api/v1/network-device?family=Wireless Controller"
    response = requests.get(url_inventory, headers=header, verify=False)
    devices = response.json().get("response", [])

    for c in devices:
        if c.get('hostname').startswith(dc):
            wlc.append(c)
        else:
            # print('dc not found') WHY THIS STILL PRINT, WHEN IT MATCHES ABOVE IF
            print(c.get('hostname'))

    return wlc

def wlc_id(wlc_ip):

    function.get_token()
    url_inventory = f"https://{Config.dnac_IP}/api/v1/network-device/ip-address/{wlc_ip}"
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
    url_inventory = f"https://{Config.dnac_IP}/api/v1/interface/network-device/{wlc_id}"

    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }

    response = requests.get(url_inventory, headers=header, verify=False)

    response = response.json().get('response')

    return response


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
    else:
        print('no site')
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