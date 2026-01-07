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
    sg_access = 0
    sg_core = 0 
    sg_dist = 0 
    sg_router = 0 
    sg_wlc = 0 
    sg_ap = 0
    sg_access_tot = 0
    sg_core_tot = 0 
    sg_dist_tot = 0 
    sg_router_tot = 0 
    sg_wlc_tot = 0 
    sg_ap_tot = 0
    header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': Config.token
        }
    url = f"{Config.dnac}/intent/api/v1/site-health"
    response = requests.get(url, headers=header, verify=False)
    site_health = response.json().get("response")
    for site in site_health:
        if not site.get("accessGoodCount"):
            site["accessGoodCount"] = 0
        if not site.get("coreGoodCount"):
            site["coreGoodCount"] = 0
        if not site.get("distributionGoodCount"):
            site["distributionGoodCount"] = 0
        if not site.get("routerGoodCount"):
            site["routerGoodCount"] = 0
        if not site.get("wlcDeviceGoodCount"):
            site["wlcDeviceGoodCount"] = 0
        if not site.get("apDeviceGoodCount"):
            site["apDeviceGoodCount"] = 0
        if not site.get("accessTotalCount"):
            site["accessTotalCount"] = 0
        if not site.get("coreTotalCount"):
            site["coreTotalCount"] = 0
        if not site.get("distributionTotalCount"):
            site["distributionTotalCount"] = 0
        if not site.get("routerTotalCount"):
            site["routerTotalCount"] = 0
        if not site.get("wlcDeviceTotalCount"):
            site["wlcDeviceTotalCount"] = 0
        if not site.get("apDeviceTotalCount"):
            site["apDeviceTotalCount"] = 0    
        if "Indonesia" in site["siteName"]:
            site_list.append({
                "site": "ID",
                "numberOfNetworkDevice": site.get("numberOfNetworkDevice"),
                "accessGoodCount": site.get("accessGoodCount"),
                "coreGoodCount": site.get("coreGoodCount"),
                "distributionGoodCount": site.get("distributionGoodCount"),
                "routerGoodCount": site.get("routerGoodCount"),
                "wlcDeviceGoodCount": site.get("wlcDeviceGoodCount"),
                "apDeviceGoodCount": site.get("apDeviceGoodCount"),
                "accessTotalCount": site.get("accessTotalCount"),
                "coreTotalCount": site.get("coreTotalCount"),
                "distributionTotalCount": site.get("distributionTotalCount"),
                "routerTotalCount": site.get("routerTotalCount"),
                "wlcDeviceTotalCount": site.get("wlcDeviceTotalCount"),
                "apDeviceTotalCount": site.get("apDeviceTotalCount")
            })
        elif "Hongkong" in site["siteName"]:
            site_list.append({
                "site": "HK",
                "numberOfNetworkDevice": site.get("numberOfNetworkDevice"),
                "accessGoodCount": site.get("accessGoodCount"),
                "coreGoodCount": site.get("coreGoodCount"),
                "distributionGoodCount": site.get("distributionGoodCount"),
                "routerGoodCount": site.get("routerGoodCount"),
                "wlcDeviceGoodCount": site.get("wlcDeviceGoodCount"),
                "apDeviceGoodCount": site.get("apDeviceGoodCount"),
                "accessTotalCount": site.get("accessTotalCount"),
                "coreTotalCount": site.get("coreTotalCount"),
                "distributionTotalCount": site.get("distributionTotalCount"),
                "routerTotalCount": site.get("routerTotalCount"),
                "wlcDeviceTotalCount": site.get("wlcDeviceTotalCount"),
                "apDeviceTotalCount": site.get("apDeviceTotalCount")
            })
        elif "Thailand" in site["siteName"]:
            site_list.append({
                "site": "TH",
                "numberOfNetworkDevice": site.get("numberOfNetworkDevice"),
                "accessGoodCount": site.get("accessGoodCount"),
                "coreGoodCount": site.get("coreGoodCount"),
                "distributionGoodCount": site.get("distributionGoodCount"),
                "routerGoodCount": site.get("routerGoodCount"),
                "wlcDeviceGoodCount": site.get("wlcDeviceGoodCount"),
                "apDeviceGoodCount": site.get("apDeviceGoodCount"),
                "accessTotalCount": site.get("accessTotalCount"),
                "coreTotalCount": site.get("coreTotalCount"),
                "distributionTotalCount": site.get("distributionTotalCount"),
                "routerTotalCount": site.get("routerTotalCount"),
                "wlcDeviceTotalCount": site.get("wlcDeviceTotalCount"),
                "apDeviceTotalCount": site.get("apDeviceTotalCount")
            })
        elif "Malaysia" in site["siteName"]:
            site_list.append({
                "site": "MY",
                "numberOfNetworkDevice": site.get("numberOfNetworkDevice"),
                "accessGoodCount": site.get("accessGoodCount"),
                "coreGoodCount": site.get("coreGoodCount"),
                "distributionGoodCount": site.get("distributionGoodCount"),
                "routerGoodCount": site.get("routerGoodCount"),
                "wlcDeviceGoodCount": site.get("wlcDeviceGoodCount"),
                "apDeviceGoodCount": site.get("apDeviceGoodCount"),
                "accessTotalCount": site.get("accessTotalCount"),
                "coreTotalCount": site.get("coreTotalCount"),
                "distributionTotalCount": site.get("distributionTotalCount"),
                "routerTotalCount": site.get("routerTotalCount"),
                "wlcDeviceTotalCount": site.get("wlcDeviceTotalCount"),
                "apDeviceTotalCount": site.get("apDeviceTotalCount")
            })
        elif site["siteName"] == "Regional Data Center Singapore" or site["siteName"] == "AXA Group Operations Singapore":
            sg_total += site.get("numberOfNetworkDevice")
            sg_access += site.get("accessGoodCount")
            sg_core += site.get("coreGoodCount")
            sg_dist += site.get("distributionGoodCount")
            sg_router += site.get("routerGoodCount")
            sg_wlc += site.get("wlcDeviceGoodCount")
            sg_ap += site.get("apDeviceGoodCount")
            sg_access_tot += site.get("accessTotalCount")
            sg_core_tot += site.get("coreTotalCount")
            sg_dist_tot += site.get("distributionTotalCount")
            sg_router_tot += site.get("routerTotalCount")
            sg_wlc_tot += site.get("wlcDeviceTotalCount")
            sg_ap_tot += site.get("apDeviceTotalCount")
            site_list.append({
                "site": "SG",
                "numberOfNetworkDevice": sg_total,
                "accessGoodCount": sg_access,
                "coreGoodCount": sg_core,
                "distributionGoodCount": sg_dist,
                "routerGoodCount": sg_router,
                "wlcDeviceGoodCount": sg_wlc,
                "apDeviceGoodCount": sg_ap,
                "accessTotalCount": sg_access_tot,
                "coreTotalCount": sg_core_tot,
                "distributionTotalCount": sg_dist_tot,
                "routerTotalCount": sg_router_tot,
                "wlcDeviceTotalCount": sg_wlc_tot,
                "apDeviceTotalCount": sg_ap_tot
            })
        elif "Philippines" in site["siteName"]:
            site_list.append({
                "site": "PH",
                "numberOfNetworkDevice": site.get("numberOfNetworkDevice"),
                "accessGoodCount": site.get("accessGoodCount"),
                "coreGoodCount": site.get("coreGoodCount"),
                "distributionGoodCount": site.get("distributionGoodCount"),
                "routerGoodCount": site.get("routerGoodCount"),
                "wlcDeviceGoodCount": site.get("wlcDeviceGoodCount"),
                "apDeviceGoodCount": site.get("apDeviceGoodCount"),
                "accessTotalCount": site.get("accessTotalCount"),
                "coreTotalCount": site.get("coreTotalCount"),
                "distributionTotalCount": site.get("distributionTotalCount"),
                "routerTotalCount": site.get("routerTotalCount"),
                "wlcDeviceTotalCount": site.get("wlcDeviceTotalCount"),
                "apDeviceTotalCount": site.get("apDeviceTotalCount")
            })
    return site_list
