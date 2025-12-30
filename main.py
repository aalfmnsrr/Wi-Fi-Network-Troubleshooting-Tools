from flask import Flask, render_template, request, session, redirect, url_for
from config import Config
from markupsafe import Markup
from functools import wraps
import json
import function, access_point, client_function, wlcs, switch
import bcrypt
from datetime import timedelta

app = Flask(__name__, template_folder='templates/docs')
app.secret_key = Config.SECRET_KEY
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False      
app.config['SESSION_COOKIE_DOMAIN'] = None      
app.config['SESSION_COOKIE_PATH'] = '/'

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
    # function.get_devices()
    # print('dashboard called')
    return render_template("dashboard.html")


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
    # print(len(clients))
    return render_template("clients.html", clients=clients, database=branch_database)


@app.route('/client-detail/<client_mac>', methods=['POST', 'GET'])
@session_check
def device_detail(client_mac):
    client = client_function.get_client_enrichment_detail(client_mac)
    client = client["userDetails"]
    connectedAP = client["connectedDevice"][0]
    neighbor_topology = client_function.get_neighbor_topology(client["hostMac"])["nodes"]
    return render_template('client-detail.html', client=client, connectedAP=connectedAP, neighbor_nodes=neighbor_topology)

@app.route('/access-points', methods=["POST", "GET"])
@session_check
def access_points():
    access_points = access_point.get_ap()
    return render_template("access-points.html", 
                           access_points=access_points)

@app.route('/access_points/<ap_mac>/<site_id>', methods=['POST', 'GET'])
@session_check
def ap_detail(ap_mac, site_id):

    ap = function.get_device_detail(ap_mac)
    wlc_id = ap.get("connectedWlcUuid")
    wlcName = function.get_devName(wlc_id)
    wlc_dc = function.get_dc(wlc_id)
    ap_details = function.get_device(ap.get("nwDeviceId"))
    radio = access_point.get_ap_radio(ap.get("nwDeviceName"), site_id)
    return render_template('ap-detail.html', ap=ap, wlcName=wlcName, wlc_id=wlc_id, wlc_dc=wlc_dc, ap_details=ap_details, radio=radio)

@app.route('/network-devices', methods=['POST', 'GET'])
@session_check
def devices():
    devices = function.get_devices()
    return render_template("network-devices.html", devices=devices)

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
                session.permanent = True
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

@app.route('/wlc/dc=<dc>/id=<id>', methods=['POST', 'GET'])
@session_check
def wlc_ssid(dc, id):
    
    ssids = wlcs.get_ssid(id)

    interface = wlcs.wlc_int(id)
    wlc = wlcs.get_wlc(dc)

    for w in wlc:
        if id == w.get('id'):
            hostname = w.get('hostname')

    # print(hostname)
  
    return render_template("/wlc/wlc_ssid.html", hostname=hostname, ssids = ssids, int = interface)

@app.route('/wlc', methods=['POST', 'GET'])
@session_check
def wlc_home():
    return render_template("/wlc/wlc_homepage.html")

@app.route('/wlc/dc=<dc>', methods=['POST', 'GET'])
@session_check
def wlc(dc):
    
    ap_wlc = {}
    wlc = wlcs.get_wlc(dc)
    for item in wlc:
        item["dc"] = dc        

    for w in wlc:
        ip = w['managementIpAddress']
        ap_wlc[ip] = wlcs.get_AP_in_WLC(ip)
        # print(ip)
        wlc_health = wlcs.health_wlc(dc, ip)

    aps = access_point.get_ap()

    return render_template("/wlc/wlc_dashboard.html",  wlcs = wlc, wlc_health = wlc_health, ap_wlc = ap_wlc, aps = aps)

# Alif
@app.route('/switches', methods=['POST', 'GET'])
def switches():
    role_filter = request.args.get('role')
    devices = switch.get_switches(role = role_filter)
    return render_template("switches.html", devices=devices)

@app.route('/switches/<device_id>', methods=['GET'])
def switch_detail(device_id):
    device = switch.get_switch_details(device_id)

    device_mac = device.get('macAddress')
    sw = switch.get_switch_health(device_mac)

    vlans = switch.get_vlan(device_id)
    vlan_count = len(vlans)
    
    return render_template("sw-details.html", device=device, sw=sw, vlan_count=vlan_count)

@app.route('/switches/<device_id>/vlans', methods=['GET'])
def switch_vlans(device_id):
    device = switch.get_switch_details(device_id)
    vlans = switch.get_vlan(device_id)
    
    return render_template("sw-vlan.html", device=device, vlans=vlans)

@app.route('/search-client', methods=['GET', 'POST'])
def search_client():
    return render_template('search-client-by-mac.html')


if __name__ == '__main__':
    # index()

    app.config['DEBUG'] = True

    # error.html will be generated if error 400 or 500 if uncomment below
    # app.config['PROPAGATE_EXCEPTIONS'] = False 

    app.run(host='0.0.0.0', port=Config.port)
