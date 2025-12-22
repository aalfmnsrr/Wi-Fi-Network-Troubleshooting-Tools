
import requests
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from config import Config
from datetime import datetime, timedelta

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

def get_device(dev_id):
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

def get_device_detail(dev_mac):
    get_token()
    url = f"{Config.dnac}/intent/api/v1/device-detail?identifier=macAddress&searchBy={dev_mac}" 
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