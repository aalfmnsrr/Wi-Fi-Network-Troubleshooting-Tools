from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from config import Config
from markupsafe import Markup
from functools import wraps
import json
from flask_apscheduler import APScheduler
import function, access_point, client_function, wlcs, switch, dashboard_page
import bcrypt
from datetime import timedelta
from os.path import exists, isfile, join
from os import listdir
import threading
from pprint import pprint

app = Flask(__name__, template_folder='templates/docs')
app.secret_key = Config.SECRET_KEY
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False # should be set to True in Production!!!!!!, this means that HTTPS is required
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config["SCHEDULER_TIMEZONE"] = "Asia/Kuala_Lumpur"
scheduler = APScheduler()

def fetch_dnac_data():
    t1 = None
    t2 = None
    t3 = None
    t4 = None
    if not exists(Config.ap_path):
        t1 = threading.Thread(target=access_point.get_ap)
        t1.start()
    if not exists(Config.wlc_path):
        t2= threading.Thread(target=wlcs.get_wlc)
        t2.start()
    if not exists(Config.switch_path):    
        t3= threading.Thread(target=switch.get_switches)
        t3.start()
    if not exists(Config.dashboard_path):
        t4= threading.Thread(target=dashboard_page.get_dashboard())
        t4.start()
    if t1:
        t1.join()
    if t2:
        t2.join()
    if t3:
        t3.join()
    if t4:
        t4.join()

# run at 12am daily
@scheduler.task("cron", id="fetch_dnac_data", hour="0", minute="0", misfire_grace_time=900, max_instances=1)
def scheduled_fetch():
    fetch_dnac_data()

def session_check(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        if "email" in session:
            return func(*args, **kwargs)
        else:
            return redirect(url_for("sign_in"))
    return decorator

@app.route('/dashboard', methods=['POST', 'GET'])
@session_check
def dashboard():
    dashboard_json = None
    with open(Config.dashboard_path, 'r', encoding="utf-8") as f:
        dashboard_json = json.load(f)
    return render_template("dashboard.html",
                           overall=dashboard_json.get("overall"),
                           access=dashboard_json.get("access"),
                           core=dashboard_json.get("core"),
                           distribution=dashboard_json.get("distribution"),
                           router=dashboard_json.get("router"),
                           wlc=dashboard_json.get("wlc"),
                           ap=dashboard_json.get("ap"),
                           site_health=dashboard_json.get("site_health"),
                           clients=dashboard_json.get("clients"),
                           system=dashboard_json.get("system")
                           )

@app.route("/get-ap-by-region", methods=["GET"])
@session_check
def get_ap_by_region():
    country = request.args.get("country")
    if not country:
        return jsonify({"status": "error", "message": "Missing id"}), 400
    ap = access_point.get_ap_by_ctr(country)
    return render_template("access-points.html", access_points=ap)

@app.route("/refresh-dashboard", methods=["GET"])
@session_check
def refresh_dashboard():
    dashboard_page.fetch_dashboard()
    return jsonify({"status": "ok"})

@app.route("/refresh-ap", methods=["GET"])
@session_check
def refresh_ap():
    id = request.args.get("id")
    if not id:
        return jsonify({"status": "error", "message": "Missing id"}), 400
    mac = access_point.fetch_ap(id)
    ap_detail(mac)
    return jsonify({"status": "ok"})

@app.route("/refresh-switch", methods=["GET"])
@session_check
def refresh_switch():
    id = request.args.get("id")
    if not id:
        return jsonify({"status": "error", "message": "Missing id"}), 400
    switch.fetch_sw(id)
    switch_detail(id)
    return jsonify({"status": "ok"})

@app.route("/refresh-wlc", methods=["GET"])
@session_check
def refresh_wlc():
    id = request.args.get("id")
    if not id:
        return jsonify({"status": "error", "message": "Missing id"}), 400
    wlcs.fetch_wlc(id)
    wlc_details(id)
    return jsonify({"status": "ok"})

@app.route('/clients', methods=['POST', 'GET'])
@session_check
def clients():
    country = request.args.get('country')
    branch = request.args.get('branch')
    floor = request.args.get('floor')
    offset = request.args.get('offset')
    query_connected_ap = ""
    if country:
        query_connected_ap+= country
    if branch:
        query_connected_ap= query_connected_ap + "-" + branch
    if floor:
        query_connected_ap= query_connected_ap + "-" + floor
        query_connected_ap = query_connected_ap + "-AP*"
    else:
        query_connected_ap = query_connected_ap + "*"
    clients = client_function.get_clients(200,offset,query_connected_ap)

   

    branch_database = client_function.get_branch_database()
    # print("query",query_connected_ap)
    # print("db",branch_database)
    dbtojson = loctojson(branch_database)
    listsc = clientlist(dbtojson)
    # print("dbtojson",json.dumps(listsc, indent=2))

    # clients = []
    if query_connected_ap == "*":
            clients = allclient(listsc)

        
    print(len(clients))
    # print("dbtojson",json.dumps(clients, indent=2))

    

    return render_template("clients.html", clients=clients, database=branch_database, dbinjson = dbtojson)

    
@app.route('/clients/<AP>', methods=['POST', 'GET'])
@session_check
def clients_AP(AP):
   

    branch_database = client_function.get_branch_database()
    dbtojson = loctojson(branch_database)
    listsc = clientlist(dbtojson)
    # clients = []

    clients = allclient(AP)

    print(len(clients))
    # print("dbtojson",json.dumps(clients, indent=2))

    

    return render_template("clients.html", clients=clients, database=branch_database, dbinjson = dbtojson)

def allclient(data):
    # --- Simple type check ---
    if isinstance(data, str):
        data_list = [data]       # wrap string into list
    elif isinstance(data, list):
        data_list = data         # already a list
    else:
        raise TypeError("data must be a string or a list")

    offset = request.args.get('offset')

    clients = []
    print("datalist", len(data_list))

    for n in data_list:
        result = client_function.get_clients(200, offset, n)
        if not result: #if no client connected to AP
            continue

        # Keep only connected clients
        for r in result:
            if isinstance(r, dict) and r.get('connectionStatus', '').lower() == 'connected':
                clients.append(r)

    print(n)
    return clients

def clientlist(db):

    out = []
    for country, sites in db.items():
        for site, floors in sites.items():
            for floor in floors:
                out.append(f"{country}-{site}-{floor}-AP*")
    print(len(out))

    return out

def loctojson(data):

    countries, sites_by_country, floors_by_country = data
    out = {}
    for ci, country in enumerate(countries):
        site_list = sites_by_country[ci] if ci < len(sites_by_country) else []
        floors_for_sites = floors_by_country[ci] if ci < len(floors_by_country) else []
        site_map = {}
        for si, site in enumerate(site_list):
            floors = floors_for_sites[si] if si < len(floors_for_sites) else []
            site_map[site] = floors
        out[country] = site_map
    return out




@app.route('/client-detail/<client_mac>', methods=['POST', 'GET'])
@session_check
def device_detail(client_mac):
    client = client_function.get_client_enrichment_detail(client_mac)
    issues = client["issueDetails"]
    client = client["userDetails"]
    health = client.get("healthScore")

    # print("dbtojson",json.dumps(client, indent=2))
    overallScore = 0
    onboardedScore = 0
    connectedScore = 0
    for h in health:
        if h["healthType"] == "OVERALL":
            overallScore = h["score"]
        elif h["healthType"] == "ONBOARDED":
            onboardedScore = h["score"]
        elif h["healthType"] == "CONNECTED":
            connectedScore = h["score"]
    connectedAP = client["connectedDevice"][0]
    neighbor_topology = client_function.get_neighbor_topology(client["hostMac"])["nodes"]
    tx = []
    rx = []
    with open(Config.ap_path, 'r', encoding="utf-8") as f:
        aps = json.load(f)
    client_links = client_function.get_client_enrichment_detail(client_mac)

    client_details = client_links.get('userDetails')
    client_connected = client_links.get('connectedDevice')[0].get('deviceDetails').get('neighborTopology')[0].get('nodes')
    phy_link = client_links.get('connectedDevice')[0].get('deviceDetails').get('neighborTopology')[0].get('links')

    #for the pysical int between ap and sw
    for p in phy_link:
        if p.get('sourceLinkStatus') == 'UP':
            phy_link = p
    # print(json.dumps(phy_link, indent=2))


    # event
    # print(client_mac)
    event = client_function.event(client_mac)
    # print("dbtojson",json.dumps(event, indent=2))

    event_child = client_function.clientevent(event)
    # print("dbtojson",json.dumps(event_child, indent=2))


    


    #to clean the array to be used in topology
    for n in client_connected[:]:
        if n.get('id') == 'client5ghz' or n.get('name') == '2.4GHz Clients':
            client_connected.remove(n)

    ssid = None

    for n in neighbor_topology:
        if n.get('role') == 'CLIENT':
            client_connected.insert(0,n)

        elif n.get('role') == 'SSID' :
            ssid = n
    # print(ssid)

    for n in client_connected:
        if n.get('role') == 'CLIENT' and ssid is not None:
            n['ssid'] = ssid['name']
        elif n.get('description') == 'AP':
            n.update(phy_link)


    from collections import defaultdict

    topology = defaultdict(list)

    
    # test = allclient('HK-ASD-18F-AP02')
    # # print(json.dumps(test, indent=2))
    # print(len(test))

    with open(Config.switch_path, 'r', encoding="utf-8") as f:
        devices = json.load(f)

    # to find connected AP to each sw
    # AP = cdp.get


    # print(client_connected)


    # topology = {}        
    for n in client_connected:
        tooltip = {
            'User': n.get('userId'),
            'IPv4': n.get('ip'),
            'Health': n.get('healthScore'),
        }   

        if n['role'] == 'CLIENT':
    
            n['icon'] = '/static/assets/img/devices/laptop.png' #to differetiate with phone/other device
            n['url'] = url_for('device_detail', client_mac = client_mac)
            tooltip['SSID'] = (ssid or {}).get('name', '')
            tooltip['Frequency'] = (ssid or {}).get('radioFrequency', '')
            tooltip = {k: v for k, v in tooltip.items() if v not in (None, '', [])}
            n['tooltip'] = tooltip
            print(tooltip)
            topology['CLIENT'].append(n)
        elif n['family'] == 'Unified AP':
            n['icon'] = '/static/assets/img/devices/access.png'
            n['url'] = url_for('ap_detail', ap_mac = n.get('additionalInfo').get('macAddress'))
            n['urlClient']= url_for('clients_AP', AP = n.get('name'))
            clientneighbor = allclient(n.get('name'))
            print("client", len(clientneighbor))
            tooltip['Client Count'] = len(clientneighbor)
            tooltip = {k: v for k, v in tooltip.items() if v not in (None, '', [])}
            n['tooltip'] = tooltip
            print(tooltip)
            topology['AP'].append(n)
        elif n['family'] == 'Switches and Hubs':
            n['icon'] = '/static/assets/img/devices/switch.png'
            n['url'] = url_for('switch_detail', device_id = n.get('id'))

            for s in devices:
                if s["id"] == n["id"]:
                    sw = s
                    break
            connectedAP = sw.get("AP")
            APintooltip = []
            APid = []
            APinnode = {}

            for c in connectedAP:
                label = c.get('label')
                mac = c.get('additionalInfo').get('macAddress')
                APintooltip.append(label)
                APid.append(mac)
                APinnode[label] = url_for('ap_detail', ap_mac = mac)

            # print(APid)
            # print(APintooltip)
            # print(APinnode)
            n['APinnode'] = APinnode

            
            tooltip['AP'] = sorted(APintooltip)

            tooltip = {k: v for k, v in tooltip.items() if v not in (None, '', [])}
            n['tooltip'] = tooltip
            topology['SWITCH'].append(n)
        elif n['family'] == 'Wireless Controller':
            n['icon'] = '/static/assets/img/devices/wlc.png'
            n['url'] = url_for('wlc_details', id = n.get('id'))
            tooltip = {k: v for k, v in tooltip.items() if v not in (None, '', [])}
            n['tooltip'] = tooltip
            print(tooltip)
            topology['WLC'].append(n)
 
    topology = dict(topology)

    def checkNull(x):
        if not x:               # catches None, {}, "", 0, False
            return "Disconnected"
        return x

    nodes = []
    for role, items in topology.items():
        for item in items:
            node_id = checkNull(item.get("name"))
            nodes.append({
                "data": {
                    "id": str(node_id),
                    "label": item.get("name", str(node_id)),
                    "role": role,
                    # include other fields if you like:
                    **{k: v for k, v in item.items() if k not in ("id", "name")}
                }
            })
           

    clients = topology.get("CLIENT", [])
    ap     = topology.get("AP", [])
    switches= topology.get("SWITCH", [])
    wlcs    = topology.get("WLC", [])

    
    def get_id(x):
        if not x.get("name"):               # catches None, {}, "", 0, False
            return "Disconnected"
        return x.get("name",  "Disconnected")



        
    # Debug: see what's available
    # print("CLIENT =", clients)
    # print("AP      =", len(ap))
    # print("SWITCH  =", len(switches))
    # print("WLC     =", len(wlcs))

    


    edges = []
    # Use the shortest chain length to avoid index errors
    chain_len = min(len(clients), len(ap), len(switches), len(wlcs)) if wlcs else min(len(clients), len(ap), len(switches)) if switches else min(len(clients), len(ap)) if ap else 0
    print("chain_len", chain_len)
    for i in range(chain_len):
        c = clients[i]; a = ap[i]
        edges.append({ "data": {
            "id": f"{get_id(c)}__to__{get_id(a)}",
            "source": checkNull(c.get('name')), "target": a.get('name'),
            "label": f"SSID: {c.get('ssid')}"
        }})
        if switches:
            s = switches[i]
            edges.append({ "data": {
                "id": f"{get_id(a)}__to__{get_id(s)}",
                "source": a.get('name'), "target": s.get('name'),
                "label": f"{a.get('sourceInterfaceName')} → {a.get('targetInterfaceName')}"
            }})
            if wlcs:
                w = wlcs[i]
                edges.append({ "data": {
                    "id": f"{get_id(s)}__to__{get_id(w)}",
                    "source": s.get('name'), "target": w.get('name'),
                    "label": ""
                    
                }})

    elements = {"nodes": nodes, "edges": edges}
    json_text = json.dumps(elements, ensure_ascii=False, indent=2)
    # print(json_text)                                


        # elif n.get('role') == 'SSID' :
        #     client_connected.insert(1,n)

    # print(json.dumps(topology['WLC'][0], indent=2))

    # print(json.dumps(client_details, indent=2))
    # print(json.dumps(client_connected, indent=2))





    txbyte = float(client_details.get('txBytes')) / (1024 * 1024)
    rxbyte = float(client_details.get('rxBytes')) / (1024 * 1024)

    tx.append(txbyte)
    rx.append(rxbyte)
    dataRate = client_details.get("dataRate")

    # print(nodes)

    return render_template('client-detail.html', event = event_child,elements = elements, tx = tx, rx =rx, link = phy_link, details = client_details, connected = client_connected, aps = aps, client=client, connectedAP=connectedAP, neighbor_nodes=neighbor_topology, overallScore=overallScore, onboardedScore=onboardedScore, connectedScore=connectedScore, dataRate=dataRate,issues=issues)

@app.route('/access-points', methods=["POST", "GET"])
@session_check
def access_points():
    aps = access_point.get_ap_by_ctr("All")
    return render_template("access-points.html",
                           access_points=aps)

@app.route('/bad-device/<site>/<devType>', methods=["POST", "GET"])
@session_check
def bad_device(site, devType):
    bad_dev = []
    if devType == "AP":
        with open(Config.ap_path, 'r', encoding="utf-8") as f:
            access_points = json.load(f)
        for ap in access_points:
            if ap.get("location") == site:
                if ap.get("details").get("overallHealth") < 8:
                    bad_dev.append(ap)
        return render_template("bad-dev.html",
                            access_points=bad_dev,
                            family="AP")
    elif devType == "Distribution" or devType == "Core" or devType == "Access" :
        devices = switch.get_sw_by_role(devType)
        sw_loc = switch.get_swLocation(devices)
        for dev in devices:
            dev_id = dev.get("id")
            location = sw_loc.get(dev_id)
            if site == "Hong Kong":
                site = "Hongkong"
            if location == site:
                if dev.get("details").get("overallHealth") < 8:
                    bad_dev.append(dev)
        return render_template("bad-dev.html",
                               devices=bad_dev,
                               family = "Switches")
    elif devType == "WLC":
        with open(Config.wlc_path, 'r', encoding="utf-8") as f:
            wlc_list = json.load(f)
        for wlc in wlc_list:
            if wlc.get("dc") == site:
                if wlc.get("details").get("overallHealth") < 8:
                    bad_dev.append(wlc)
        return render_template("bad-dev.html",
                            wlc=bad_dev,
                            family="WLC")

@app.route('/access_points/<ap_mac>', methods=['POST', 'GET'])
@session_check
def ap_detail(ap_mac):
    ap = {}
    ap_details = {}
    id = ""
    site_id = ""
    with open(Config.ap_path, 'r', encoding="utf-8") as f:
        ap_json = json.load(f)
    for a in ap_json:
        if a.get("additionalInfo").get("macAddress").upper() == ap_mac.upper():
            site_id = a.get("additionalInfo").get("siteid")
            id = a.get("id")
            ap = a.get("details")
            break
    wlc_id = ap.get("connectedWlcUuid")
    wlcName = function.get_devName(wlc_id, "WLC")
    wlc_dc = function.get_dc(wlc_id)
    issues = access_point.get_Issues(ap.get("nwDeviceId"))
    ap_details = function.append_AP_dev(ap.get("nwDeviceId"), "AP")
    radios = access_point.get_ap_radio(ap.get("nwDeviceName"), site_id)
    clientneighbor = allclient(ap.get('nwDeviceName'))
    clientcount = len(clientneighbor)
    return render_template('ap-detail.html', ap=ap, wlcName=wlcName, clientcount=clientcount, clientneighbor=clientneighbor, ap_details=ap_details, wlc_id=wlc_id, wlc_dc=wlc_dc, radio=radios, issues=issues, id=id)

@app.route('/', methods=["POST", "GET"])
def sign_in():
    date = function.get_date()
    message = 'Sign in to your account to continue'
    if "email" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        user = Config.users.get(email.lower())
        if user:
            if bcrypt.checkpw(password.encode("utf-8"), user["password"]):
                session.permanent = False
                session["email"] = user["email"]
                session["username"] = user["name"]
                function.append_file(
                    f"{Config.script_path}/logs.txt",
                    "[{}-{}-{}-{}] User {} has been logged in\n".format(
                        date["year"], date["month"], date["day"], date["time"], session["username"]
                    ),
                )
                return redirect(url_for("dashboard"))
            else:
                message = Markup('<div class="text-center alert alert-danger"><p>Email not found.</p></div>')
                function.append_file(
                    f"{Config.script_path}/logs.txt",
                    "[{}-{}-{}-{}] Email {} not found during login\n".format(
                        date["year"], date["month"], date["day"], date["time"],
                        email,
                    ),
                )
                return render_template("sign-in.html", message=message)
        else:
            message = Markup(
                '<div class="d-flex justify-content-center"><div class="alert alert-danger text-center mx-3"><p>Email not found.</p></div></div>')
            return render_template("sign-in.html", message=message)
    return render_template("sign-in.html", message=message)

@app.route("/signout", methods=["POST", "GET"])
def signout():
    if "email" in session:
        session.pop("email", None)
        session.pop("username", None)
        return render_template("sign-in.html")
    else:
        return render_template("sign-in.html")

@app.route('/wlc', methods=['POST', 'GET'])
@session_check
def wlc_list():
    with open(Config.wlc_path, 'r', encoding="utf-8") as f:
        wlc = json.load(f)
    return render_template("/wlc/wlc_list.html", wlc = wlc)


@app.route('/wlc/id=<id>', methods=['POST', 'GET'])
@session_check
def wlc_details(id):
    wlc = None
    ssids = None
    interface = None
    physical = None
    ap_wlc = None
    aps = None
    health = None
    with open(Config.wlc_path, 'r', encoding="utf-8") as f:
        device = json.load(f)
    for w in device:
        if w["id"] == id:
            wlc = w
            break
    id = wlc.get("id")
    d = wlc.get("upTime")
    ssids = wlc.get("ssid")
    interface = wlc.get("interface")
    physical = wlc.get("physical")
    ap_wlc = wlc.get("AP")
    health = wlc.get("health")
    with open(Config.ap_path, 'r', encoding="utf-8") as f:
        aps = json.load(f)
    for i in interface:
        i['formattedSpeed'] = switch.format_speed_kbps(i.get('speed'))

    cdp = wlc.get('cdp')
    
    return render_template("/wlc/wlc_details.html", device = wlc, cdp=cdp, id= id, d = d, aps = aps, wlc = wlc, ap_wlc = ap_wlc, health = health, ssids = ssids, int = interface, physical = physical)

# @app.route('/wlc/dc=<dc>/id=<id>', methods=['POST', 'GET'])
# @session_check
# def wlc_ssid(dc, id):
#     wlc = None
#     ssids = None
#     interface = None
#     physical = None
#     hostname = None
#     series = None
#     with open(Config.wlc_path, 'r', encoding="utf-8") as f:
#         device = json.load(f)
#     for w in device:
#         if w["id"] == id:
#             wlc = w
#             ssids = w.get("ssid")
#             interface = w.get("interface")
#             physical = w.get("physical")
#             hostname = w.get('name')
#             series = w.get('deviceSeries')
#     return render_template("/wlc/wlc_ssid.html", wlcs = wlc, s = series, hostname=hostname, ssids = ssids, int = interface, physical = physical)



# @app.route('/wlc/dc=<dc>', methods=['POST', 'GET'])
# @session_check
# def wlc(dc):
#     ap_wlc = {}
#     wlc = []
#     with open(Config.wlc_path, 'r', encoding="utf-8") as f:
#         all_wlc = json.load(f)
#     for w in all_wlc:
#         if w.get('hostname').startswith(dc):
#             wlc.append(w)
#     for w in wlc:
#         ip = w['managementIpAddress']
#         ap_wlc[ip] = wlcs.get_AP_in_WLC(ip)
#         # print(ip)
#         wlc_health = wlcs.health_wlc(dc, ip)
#     with open(Config.ap_path, 'r', encoding="utf-8") as f:
#         aps = json.load(f)
#     return render_template("/wlc/wlc_dashboard.html",  wlcs = wlc, wlc_health = wlc_health, ap_wlc = ap_wlc, aps = aps, dc = dc)

# Alif
@app.route('/switches', methods=['POST', 'GET'])
@session_check
def switches():
    devices = None
    role = request.args.get("role")
    with open(Config.switch_path, 'r', encoding="utf-8") as f:
        devices = json.load(f)
    
    
    # Filter if a role is provided (safer normalization)
    if role:
        role_norm = (role or "").strip().upper()
        devices = [
            d for d in devices
            if (d.get("role") or "").strip().upper() == role_norm
        ]
    else:
        role_norm = None  # for logging only


    sw_locations = switch.get_swLocation(devices)

    return render_template("switches.html", devices=devices, sw_locations=sw_locations, role=role)

@app.route('/switches/<device_id>', methods=['GET'])
@session_check
def switch_detail(device_id):
    device = None
    ap_cnt = None
    ap_groups = None
    vlans = None
    vlan_count = None
    poe = None
    issues = None
    stack_json = None
    stack_info = None
    svl_info = None
    use_svl = None
    sw_interface = None
    sw = None
    access_points = None
    pwrSply = None
    cdp = None

    with open(Config.switch_path, 'r', encoding="utf-8") as f:
        device = sw = json.load(f)
    for d in device:
        if d["id"] == device_id:
            sw = d.get("details")
            
            access_points = d.get("AP")
            ap_cnt = len(access_points)
            ap_groups = switch.group_ap_labels_by_floor(access_points)
            
            vlans = d.get("vlans")
            vlan_count = len(vlans)
            
            poe = d.get("poe")
            
            issues = switch.get_switchIssues(device_id)
            
            stack_json = d.get("stack_json")
            stack_info = d.get("stack_info")
            svl_info = d.get("svl_info")
            use_svl = bool(stack_json.get('svlSwitchInfo')) and bool(svl_info)
            
            sw_interface = d.get("interface")
            
            pwrSply = switch.sort_power_supplies(d.get("powerSupply"))
            
            cdp = d.get("cdp") or []
            
            device = d
            
            break
    
    # Decorate each interface with a formatted speed string
    # Ensure sw_interface is a list/dict iterable; adjust if your structure is different
    if isinstance(sw_interface, list):
        for intf in sw_interface:
            intf['speed_fmt'] = switch.format_speed_kbps(intf.get('speed'))
    elif isinstance(sw_interface, dict):
        # In some payloads interfaces are under a key like 'interfaces'
        interfaces = sw_interface.get('interfaces', [])
        for intf in interfaces:
            intf['speed_fmt'] = switch.format_speed_kbps(intf.get('speed'))
        # If you want to render the nested list, reassign:
        sw_interface = interfaces

    return render_template("sw-details.html", device=device, sw=sw, access_points=access_points, ap_cnt=ap_cnt,
    ap_groups=ap_groups, vlan_count=vlan_count, stack_json=stack_json, stack_info=stack_info, svl_info=svl_info,
    use_svl=use_svl, device_id=device_id, sw_interface=sw_interface, poe=poe, issues=issues, pwrSply=pwrSply, cdp=cdp)

@app.route('/switches/<device_id>/aps', methods=['GET'])
@session_check
def switch_access_points(device_id):
    # APs connected to this switch only
    sw = function.get_device(device_id, "Switch")
    aps = switch.get_ap_neighbors(device_id)
    return render_template("access-points.html", access_points=aps, source_switch=device_id, sw=sw)

@app.route('/switches/<device_id>/vlans', methods=['GET'])
def switch_vlans(device_id):
    device = function.get_device(device_id, "Switch")
    vlans = switch.get_vlan(device_id)

    return render_template("sw-vlan.html", device=device, vlans=vlans)

@app.route('/search-client', methods=['GET', 'POST'])
def search_client():
    return render_template('search-client-by-mac.html')


if __name__ == '__main__':
    app.config['DEBUG'] = True
    # error.html will be generated if error 400 or 500 if uncomment below
    # app.config['PROPAGATE_EXCEPTIONS'] = False
    # run when app loads
    fetch_dnac_data()
    scheduler.init_app(app)
    if not scheduler.running:
        scheduler.start()
    app.run(host='0.0.0.0', port=Config.port)
