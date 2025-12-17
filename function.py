
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
import requests, json
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from config import Config

def get_ap():
    get_token()
    url = f"{Config.dnac}/intent/api/v1/topology/physical-topology"
    header = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Auth-Token': Config.token
    }
    response = requests.get(url, headers=header, verify=False).json().get("response").get("nodes")
    for r in response:
        if "MY-PCH-10F-AP" in r["label"] or "MY-PCH-13AF-AP" in r["label"]:
            Config.access_points.append(r)
    print(len(Config.access_points))
    ind = 0
    while ind < len(Config.access_points) - 1:
        current_ap = Config.access_points[ind]
        next_ap = Config.access_points[ind+1]
        if current_ap == next_ap:
            Config.access_points.remove(next_ap)
        ind += 1

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
    url = f'{Config.dnac}/intent/api/v1/client-enrichment-details'
    client_response = requests.get(url, headers=header, verify=False)
    client = client_response.json()[0]
    # print(client)
    return client


# get clients of an AP
def get_clients():
    get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
    }
    url = f'{Config.dnac}/data/api/v1/clients'
    clients_response = requests.get(url, headers=header, verify=False).json()
    clients = clients_response["response"]
    for client in clients:
        connectedDevice = client.get('connectedNetworkDevice', {})
        if "MY-PCH-" in connectedDevice.get('connectedNetworkDeviceName'):
            Config.clients.append(client)
    # print(len(Config.clients))

def get_devices(): # network devices
    get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    url_inventory = f"{Config.dnac}/intent/api/v1/network-device"
    response = requests.get(url_inventory, headers=header, verify=False)
    Config.devices = response.json().get("response", [])
    # print(response.text)

def get_wlc(): #get wlc
    get_devices()
    # print(Config.devices)

    Config.wlc = []

    for c in Config.devices:
        if c.get('hostname').startswith("APDC"):
            Config.wlc.append(c)
            # print(json.dumps(c, indent=2))

    wlc_IP=[]

    for c in Config.wlc:
        IP = c.get('managementIpAddress')
        wlc_IP.append(IP)

    # print(Config.wlc)
    
    # return wlc_IP

    # print (get_wlc()[1]) ['10.54.241.253', '10.54.242.253']


def wlc_id(wlc_ip):

    get_token()
    get_wlc()
    url_inventory = f"https://{Config.dnac_IP}/api/v1/network-device/ip-address/{wlc_ip}"
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }

    response = requests.get(url_inventory, headers=header, verify=False)

    # print(json.dumps(response.json(), indent=2))

    wlc_id = response.json().get('response').get('id')
    # print(wlc_id)
    return wlc_id

def wlc_int(wlc_id):

    get_token()
    get_wlc()
    
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

    get_token()
    get_wlc()

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

    get_token()
    get_wlc()
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
        if "MY-PCH-10F-AP" in r["hostname"]:
            ap_wlc.append(r)
        elif "MY-PCH-13AF-AP" in r["hostname"]:
            ap_wlc.append(r)

    return ap_wlc


def health_wlc(wlc_ip):
    #note that both AP wlc has the same site id
    get_token()
    get_wlc()

    url = f"{Config.dnac}/intent/api/v1/topology/physical-topology"
    header = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Auth-Token': Config.token
    }

    health = []

    response = requests.get(url, headers = header, verify = False).json().get('response').get('nodes')

    for r in response:
        if "APDC3S12-WLC" in r["label"]:
            siteId = r["additionalInfo"]["siteid"]
    
    url_health = f"{Config.dnac}/intent/api/v1/device-health?siteId={siteId}" 

    response_health = requests.get(url_health, headers = header, verify = False).json().get('response')
    #one site id contains both ap wlc
    
    return response_health

def wlc_int(wlc_id):
    get_token()
    get_wlc()

    url = f"{Config.dnac}/intent/api/v1/interface/network-device/{wlc_id}"
    header = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Auth-Token': Config.token
    } 

    response = requests.get(url, headers = header, verify = False).json().get('response')

    # for r in response:
    #     print(r.get("portName"))

    return response


# wlc_int('baa57c39-1a79-41df-9f56-4bbadd26d84f')

# print(health_wlc('10.54.241.253')[1])
# wlc_id('10.54.241.253')

# wlc_int(wlc_id('10.54.241.253'))


# get_wlc()

# print(get_AP_in_WLC("10.54.242.253"))

