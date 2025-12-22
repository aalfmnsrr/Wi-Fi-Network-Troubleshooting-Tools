import function
import requests
from config import Config

def get_client_enrichment_detail(client_mac):
    function.get_token()
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
    function.get_token()
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