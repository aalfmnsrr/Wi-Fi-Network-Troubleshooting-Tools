import function
import requests
from config import Config

def network_health():
    function.get_token()
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    url = f"{Config.dnac}/intent/api/v1/network-health"
    response = requests.get(url, headers=header, verify=False)
    health = response.json()
    # print(health)
    return health

def get_overall():
    health = network_health()
    health = health.get("response")[0]
    return health

def get_core():
    health = network_health()
    # print(health)
    health = health.get("healthDistirubution")
    for h in health:
        if h["category"] == "Core":
            return h

def get_access():
    health = network_health()
    # print(health)
    health = health.get("healthDistirubution")
    # print(health)
    for h in health:
        if h["category"] == "Access":
            return h
        
def get_distribution():
    health = network_health()
    health = health.get("healthDistirubution")
    for h in health:
        if h["category"] == "Distribution":
            return h
        
def get_router():
    health = network_health()
    health = health.get("healthDistirubution")
    for h in health:
        if h["category"] == "Router":
            return h
        
def get_wlc():
    health = network_health()
    health = health.get("healthDistirubution")
    for h in health:
        if h["category"] == "WLC":
            return h
        
def get_AP():
    health = network_health()
    health = health.get("healthDistirubution")
    for h in health:
        if h["category"] == "AP":
            return h
        
def get_site_health():
    function.get_token()
    site_list = []
    sg_total = 0
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    url = f"{Config.dnac}/intent/api/v1/site-health"
    response = requests.get(url, headers=header, verify=False)
    site_health = response.json().get("response")
    for site in site_health:
        if "Indonesia" in site["siteName"]:
            site_list.append({
                "site": "ID",
                "numberOfNetworkDevice": site.get("numberOfNetworkDevice")
            })
        elif "Hongkong" in site["siteName"]:
            site_list.append({
                "site": "HK",
                "numberOfNetworkDevice": site.get("numberOfNetworkDevice")
            })
        elif "Thailand" in site["siteName"]:
            site_list.append({
                "site": "TH",
                "numberOfNetworkDevice": site.get("numberOfNetworkDevice")
            })
        elif "Malaysia" in site["siteName"]:
            site_list.append({
                "site": "MY",
                "numberOfNetworkDevice": site.get("numberOfNetworkDevice")
            })
        elif site["siteName"] == "Regional Data Center Singapore" or site["siteName"] == "AXA Group Operations Singapore":
            sg_total += site.get("numberOfNetworkDevice")
            site_list.append({
                "site": "SG",
                "numberOfNetworkDevice": sg_total
            })
        elif "Philippines" in site["siteName"]:
            site_list.append({
                "site": "PH",
                "numberOfNetworkDevice": site.get("numberOfNetworkDevice")
            })
    return site_list
