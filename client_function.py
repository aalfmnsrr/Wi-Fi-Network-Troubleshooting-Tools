import requests
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from config import Config

database = [
    [],
    [],
    []
]

header = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Auth-Token': Config.token
    }

def get_client_enrichment_detail(client_mac):
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


def get_ap(limit, offset):
    """
    Get "/network-device" and filter for AP
    
    :param limit: maximum quantity of data to query (API Support max 500/query)
    :param offset: set the starting row of query (value >= 1, else error)
    """
    url = f"{Config.dnac}/intent/api/v1/network-device"
    params = {
        "limit": limit,
        "offset": offset,
        "family": "Unified AP"
    }
    response = requests.get(url, headers=header, params=params, verify=False)
    response.raise_for_status() 
    return response.json().get("response", [])

def fetch_all_ap(limit=500):
    """
    Get all existing ap using the function `get_ap`
    
    :param limit: set limit to max size
    """

    offset = 1
    while True:
        devices = get_ap(limit, offset)
        if len(devices) == 0:
            break
        yield from devices
        offset += limit
        # 1st Loop: Offset --> 1
        # 2nd Loop: Offset --> 501
        # 3rd Loop: Offset --> 1001

def get_branch_database():
    """
    Extract floor, branch, and country data from all AP Hostname


    Given hostnames:
        ID-ATO-17F-AP12
        ID-XYZ-5F-AP34
        ID-ATO-12F-AP15
    
    The resulting `database` will be:
        [
            ['ID'],                       # Countries
            [['ATO'], ['XYZ']],           # Branches for each country
            [
                [['17F', '12F']],        # Floors in 'ATO'
                [['5F']]                 # Floors in 'XYZ'
            ]
        ]

    """

    for i in list(fetch_all_ap()):
        hostname = i['hostname']
        country = hostname.split("-")[0]
        branch = hostname.split("-")[1]
        floor = hostname.split("-")[2]

        # Check if country is already in database[0]
        if country not in database[0]:
            database[0].append(country)
            database[1].append([])  # Initialize list for branches of this country
            database[2].append([])  # Initialize list for floors for this country

        # Find index of the country
        country_index = database[0].index(country)

        # Check if branch exists under this country
        if branch not in database[1][country_index]:
            database[1][country_index].append(branch)
            database[2][country_index].append([])  # Initialize list for floors of this branch

        # Find index of the branch within the country's branch list
        branch_index = database[1][country_index].index(branch)

        # Check if floor exists under this branch
        if floor not in database[2][country_index][branch_index]:
            database[2][country_index][branch_index].append(floor)

    return database


def get_clients(limit, offset, connectedAP):
    """
    Get clients with specified limit & offset, filtered based on AP Hostname 
    
    :param limit: maximum quantity of data to query (API Support max 500/query)
    :param offset: set the starting row of query (value >= 1, else error)
    :param connectedAP: Hostname of AP (ID-ATO-17F-AP12, ID*, ID-ATO-*), support wildcard suffix
    """
    url = f"{Config.dnac}/data/api/v1/clients"
    params = {
        "limit": limit,
        "offset": offset,
        "connectedNetworkDeviceName": connectedAP,
        'connectionStatus': 'connected'
    }
    response = requests.get(url, headers=header, params=params, verify=False)
    response.raise_for_status() 
    return response.json().get("response", [])


def get_neighbor_topology(client_mac):
    """
    Get client topology based on client mac address
    
    :param client_mac: mac address of client/user device
    """
    url = f"{(Config.dnac)[:-4]}/api/assurance/v1/host/{client_mac}/neighbor-topology"
    params = {

    }
    response = requests.get(url, headers=header, params=params, verify=False)
    response.raise_for_status() 
    return response.json().get("response", [])