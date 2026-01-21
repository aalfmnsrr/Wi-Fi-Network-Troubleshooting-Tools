from flask import Flask, render_template, request, session, redirect, url_for
from config import Config
from markupsafe import Markup
from functools import wraps
import json
from flask_apscheduler import APScheduler
import function, access_point, client_function, wlcs, switch, dashboard_page
import bcrypt
from datetime import timedelta
from os import makedirs

app = Flask(__name__, template_folder='templates/docs')
app.secret_key = Config.SECRET_KEY
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['SESSION_COOKIE_PATH'] = '/'
app.config["SCHEDULER_TIMEZONE"] = "Asia/Kuala_Lumpur"
scheduler = APScheduler()

def fetch_dnac_data():
    ap = access_point.get_ap()
    wlc = wlcs.get_wlc()
    sw = switch.get_switches()
    makedirs(Config.ap_path, exist_ok=True)
    makedirs(Config.wlc_path, exist_ok=True)
    makedirs(Config.switch_path, exist_ok=True)
    with open(f"{Config.ap_path}/ap.json", "w", encoding="utf-8") as f:
        json.dump(ap, f, indent=4, ensure_ascii=False, default=str)
    with open(f"{Config.wlc_path}/wlc.json", "w", encoding="utf-8") as f:
        json.dump(wlc, f, indent=4, ensure_ascii=False, default=str)
    with open(f"{Config.switch_path}/switches.json", "w", encoding="utf-8") as f:
        json.dump(sw, f, indent=4, ensure_ascii=False, default=str)

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
    overall = dashboard_page.get_overall()
    access = dashboard_page.get_access()
    core = dashboard_page.get_core()
    distribution = dashboard_page.get_distribution()
    router = dashboard_page.get_router()
    with open(f"{Config.wlc_path}/wlc.json", 'r', encoding="utf-8") as f:
        wlc = json.load(f)
    ap = dashboard_page.get_AP()
    site_health = dashboard_page.get_site_health()
    clients = dashboard_page.get_clients()
    system = dashboard_page.get_sys_performance()
    return render_template("dashboard.html",
                           overall=overall,
                           access=access,
                           core=core,
                           distribution=distribution,
                           router=router,
                           wlc=wlc,
                           ap=ap,
                           site_health=site_health,
                           clients=clients,
                           system=system
                           )

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
    clients = client_function.get_clients(200,offset,f"{query_connected_ap}")
    branch_database = client_function.get_branch_database()
    # print(clients)
    return render_template("clients.html", clients=clients, database=branch_database)

@app.route('/client-detail/<client_mac>', methods=['POST', 'GET'])
@session_check
def device_detail(client_mac):
    client = client_function.get_client_enrichment_detail(client_mac)
    issues = client["issueDetails"]
    client = client["userDetails"]
    health = client.get("healthScore")
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
    with open(f"{Config.ap_path}/ap.json", 'r', encoding="utf-8") as f:
        aps = json.load(f)
    client_links = client_function.get_client_enrichment_detail(client_mac)

    client_details = client_links.get('userDetails')
    client_connected = client_links.get('connectedDevice')[0].get('deviceDetails').get('neighborTopology')[0].get('nodes')
    phy_link = client_links.get('connectedDevice')[0].get('deviceDetails').get('neighborTopology')[0].get('links')

    #for the pysical int between ap and sw
    for p in phy_link:
        if p.get('sourceLinkStatus') == 'UP':
            phy_link = p

    #to clean the array to be used in topology
    for n in client_connected[:]:
        if n.get('id') == 'client5ghz' or n.get('name') == '2.4GHz Clients':
            client_connected.remove(n)

    # to insert topology following the order of the topology
    for n in neighbor_topology:
        if n.get('role') == 'CLIENT':
            client_connected.insert(0,n)

        elif n.get('role') == 'SSID' :
            client_connected.insert(1,n)

    txbyte = float(client_details.get('txBytes')) / (1024 * 1024)
    rxbyte = float(client_details.get('rxBytes')) / (1024 * 1024)

    tx.append(txbyte)
    rx.append(rxbyte)
    dataRate = client_details.get("dataRate")
    return render_template('client-detail.html', tx = tx, rx =rx, link = phy_link, details = client_details, connected = client_connected, aps = aps, client=client, connectedAP=connectedAP, neighbor_nodes=neighbor_topology, overallScore=overallScore, onboardedScore=onboardedScore, connectedScore=connectedScore, dataRate=dataRate,issues=issues)

@app.route('/access-points', methods=["POST", "GET"])
@session_check
def access_points():
    with open(f"{Config.ap_path}/ap.json", 'r', encoding="utf-8") as f:
        aps = json.load(f)
    return render_template("access-points.html",
                           access_points=aps)

@app.route('/bad-device/<site>/<devType>', methods=["POST", "GET"])
@session_check
def bad_device(site, devType):
    bad_dev = []
    if devType == "AP":
        with open(f"{Config.ap_path}/ap.json", 'r', encoding="utf-8") as f:
            access_points = json.load(f)
        for ap in access_points:
            if ap.get("location") == site:
                mac = ap.get("additionalInfo").get("macAddress")
                ap["macAddress"] = mac
                overallHealth = function.get_reach(mac)
                if overallHealth < 7:
                    ap["health"] = overallHealth
                    bad_dev.append(ap)
        return render_template("bad-dev.html",
                            access_points=bad_dev,
                            family="AP")
    elif devType == "Distribution" or devType == "Core" or devType == "Access" :
        devices = switch.get_switches(devType.upper())
        for dev in devices:
            dev_id = dev.get("id")
            sw_loc = switch.get_swLocation()
            location = sw_loc.get(dev_id)
            if site == "Hong Kong":
                site = "Hongkong"
            if location == site:
                mac = dev.get("macAddress")
                overallHealth = function.get_reach(mac)
                if overallHealth < 7:
                    dev["location"] = location
                    dev["health"] = overallHealth
                    bad_dev.append(dev)
        return render_template("bad-dev.html",
                               devices=bad_dev,
                               family = "Switches")
    elif devType == "WLC":
        with open(f"{Config.wlc_path}/wlc.json", 'r', encoding="utf-8") as f:
            wlc_list = json.load(f)
        for wlc in wlc_list:
            if wlc.get("dc") == site:
                mac = wlc.get("macAddress")
                overallHealth = function.get_reach(mac)
                if overallHealth < 7:
                    wlc["health"] = overallHealth
                    bad_dev.append(wlc)
        return render_template("bad-dev.html",
                            wlc=bad_dev,
                            family="WLC")

@app.route('/access_points/<ap_mac>/<site_id>', methods=['POST', 'GET'])
@session_check
def ap_detail(ap_mac, site_id):
    ap = function.get_device_detail(ap_mac)
    wlc_id = ap.get("connectedWlcUuid")
    wlcName = function.get_devName(wlc_id)
    wlc_dc = function.get_dc(wlc_id)
    issues = access_point.get_Issues(ap.get("nwDeviceId"))
    # print(wlcName)
    # print(wlc_dc)
    ap_details = function.get_device(ap.get("nwDeviceId"))
    radio = access_point.get_ap_radio(ap.get("nwDeviceName"), site_id)
    return render_template('ap-detail.html', ap=ap, wlcName=wlcName, wlc_id=wlc_id, wlc_dc=wlc_dc, ap_details=ap_details, radio=radio, issues=issues)

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

@app.route('/wlc/id=<id>', methods=['POST', 'GET'])
@session_check
def wlc_details(id):

    ssids = wlcs.get_ssid(id)
    interface = wlcs.wlc_int(id)
    wlc = wlcs.get_wlc_by_id(id)
    physical = wlcs.get_physical(id)
    ap_wlc = {}
    ap_wlc = wlcs.get_AP_in_WLC(wlc.get("managementIpAddress"))
    site = wlc.get('siteHierarchyId').strip("/").split("/")[-1]
    health = wlcs.health(site, id)

    with open(f"{Config.ap_path}/ap.json", 'r', encoding="utf-8") as f:
        aps = json.load(f)
    device = function.get_device(id)

    for i in interface:
        i['formattedSpeed'] = switch.format_speed_kbps(i.get('speed'))

    return render_template("/wlc/wlc_details.html", d = device, aps = aps, wlc = wlc, ap_wlc = ap_wlc, health = health, ssids = ssids, int = interface, physical = physical)

@app.route('/wlc/dc=<dc>/id=<id>', methods=['POST', 'GET'])
@session_check
def wlc_ssid(dc, id):

    ssids = wlcs.get_ssid(id)
    interface = wlcs.wlc_int(id)
    wlc = wlcs.get_wlc_by_id(id)
    physical = wlcs.get_physical(id)

    hostname = wlc.get('name')
    series = wlc.get('deviceSeries')

    return render_template("/wlc/wlc_ssid.html", wlcs = wlc, s = series, hostname=hostname, ssids = ssids, int = interface, physical = physical)

@app.route('/wlc', methods=['POST', 'GET'])
@session_check
def wlc_home():
    return render_template("/wlc/wlc_homepage.html")

@app.route('/wlc/list', methods=['POST', 'GET'])
@session_check
def wlc_list():
    with open(f"{Config.wlc_path}/wlc.json", 'r', encoding="utf-8") as f:
        wlc = json.load(f)
    return render_template("/wlc/wlc_list.html", wlc = wlc)

@app.route('/wlc/dc=<dc>', methods=['POST', 'GET'])
@session_check
def wlc(dc):

    ap_wlc = {}
    wlc = []
    with open(f"{Config.wlc_path}/wlc.json", 'r', encoding="utf-8") as f:
        all_wlc = json.load(f)

    for w in all_wlc:
        if w.get('hostname').startswith(dc):
            wlc.append(w)
    for w in wlc:
        ip = w['managementIpAddress']
        ap_wlc[ip] = wlcs.get_AP_in_WLC(ip)
        # print(ip)
        wlc_health = wlcs.health_wlc(dc, ip)

    with open(f"{Config.ap_path}/ap.json", 'r', encoding="utf-8") as f:
        aps = json.load(f)

    return render_template("/wlc/wlc_dashboard.html",  wlcs = wlc, wlc_health = wlc_health, ap_wlc = ap_wlc, aps = aps, dc = dc)

# Alif
@app.route('/switches', methods=['POST', 'GET'])
@session_check
def switches():
    role_filter = request.args.get('role')
    devices = switch.get_switches(role = role_filter)
    sw_locations = switch.get_swLocation()
    return render_template("switches.html", devices=devices, sw_locations=sw_locations)

@app.route('/switches/<device_id>', methods=['GET'])
@session_check
def switch_detail(device_id):
    device = function.get_device(device_id)

    device_mac = device.get('macAddress')
    sw = function.get_device_detail(device_mac)

    access_points = []
    access_points = switch.get_ap_neighbors(device_id)
    ap_cnt = len(access_points)
    ap_groups = switch.group_ap_labels_by_floor(access_points)

    vlans = switch.get_vlan(device_id)
    vlan_count = len(vlans)

    stack_json = switch.get_stack_info(device_id)
    stack_info = switch.dict_stack_summary(stack_json)
    svl_info = switch.dict_svl_summary(stack_json)
    use_svl = bool(stack_json.get('svlSwitchInfo')) and bool(svl_info)

    sw_interface = switch.get_interface(device_id)
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

    poe = switch.get_poe(device_id)

    issues = switch.get_switchIssues(device_id)

    return render_template("sw-details.html", device=device, sw=sw, access_points=access_points, ap_cnt=ap_cnt,
    ap_groups=ap_groups, vlan_count=vlan_count, stack_json=stack_json, stack_info=stack_info, svl_info=svl_info,
    use_svl=use_svl, device_id=device_id, sw_interface=sw_interface, poe=poe, issues=issues)

@app.route('/switches/<device_id>/aps', methods=['GET'])
@session_check
def switch_access_points(device_id):
    # APs connected to this switch only
    sw = function.get_device(device_id)
    aps = switch.get_ap_neighbors(device_id)
    return render_template("access-points.html", access_points=aps, source_switch=device_id, sw=sw)

@app.route('/switches/<device_id>/vlans', methods=['GET'])
def switch_vlans(device_id):
    device = function.get_device(device_id)
    vlans = switch.get_vlan(device_id)

    return render_template("sw-vlan.html", device=device, vlans=vlans)

@app.route('/search-client', methods=['GET', 'POST'])
def search_client():
    return render_template('search-client-by-mac.html')


if __name__ == '__main__':
    app.config['DEBUG'] = False
    # error.html will be generated if error 400 or 500 if uncomment below
    # app.config['PROPAGATE_EXCEPTIONS'] = False
    # run when app loads
    fetch_dnac_data()
    scheduler.init_app(app)
    if not scheduler.running:
        scheduler.start()
    app.run(host='0.0.0.0', port=Config.port)
