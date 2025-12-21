from flask import Flask, render_template, request, session, redirect, url_for
from config import Config
from markupsafe import Markup
from functools import wraps
import function, json
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
    clients = function.get_clients()
    # print(clients)
    # print(len(clients))
    return render_template("clients.html", clients=clients)

@app.route('/client-detail/<client_mac>', methods=['POST', 'GET'])
@session_check
def device_detail(client_mac):
    client = function.get_client_enrichment_detail(client_mac)
    connectedAP = client["connectedDevice"][0].get("deviceDetails")
    client = client["userDetails"]
    return render_template('client-detail.html', client=client, connectedAP=connectedAP)

@app.route('/access-points', methods=["POST", "GET"])
@session_check
def access_points():
    access_points = function.get_ap()
    # print(len(access_points))
    # print(access_points)
    return render_template("access-points.html", access_points=access_points)

@app.route('/ap-detail/<ap_mac>', methods=['POST', 'GET'])
@session_check
def ap_detail(ap_mac):
    ap = function.get_ap_detail(ap_mac)
    wlc = function.get_devName(ap.get("connectedWlcUuid"))
    ap_details = function.get_dev_details(ap.get("nwDeviceId"))
    radio = function.get_ap_radio(ap.get("nwDeviceName"))
    return render_template('ap-detail.html', ap=ap, wlc=wlc, ap_details=ap_details, radio=radio)

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
def wlc_ssid(dc, id):
    
    # id = function.wlc_id(function.get_wlc()[1])
    ssids = function.get_ssid(id)

    interface = function.wlc_int(id)
    wlc = function.get_wlc(dc)

    for w in wlc:
        if id == w.get('id'):
            hostname = w.get('hostname')

    # print(hostname)
  
    return render_template("/wlc/wlc_ssid.html", hostname=hostname, ssids = ssids, int = interface)

@app.route('/wlc', methods=['POST', 'GET'])
def wlc_home():

    return render_template("/wlc/wlc_homepage.html")

@app.route('/wlc/dc=<dc>', methods=['POST', 'GET'])
def wlc(dc):
    
    # function.get_wlc(dc)
    ap_wlc = {}
    # print(dc)
    wlc = function.get_wlc(dc)
    for item in wlc:
        item["dc"] = dc        

    for w in wlc:
        ip = w['managementIpAddress']
        ap_wlc[ip] = function.get_AP_in_WLC(ip)
        # print(ip)
        wlc_health = function.health_wlc(dc, ip)
        # print(json.dumps(wlc_health, indent=2))

    return render_template("/wlc/wlc_dashboard.html",  wlcs = wlc, wlc_health = wlc_health, ap_wlc = ap_wlc)

@app.route('/sor', methods=['POST', 'GET'])
def t():
# function.get_wlc(dc)
    ap_wlc = {}
    # print(dc)
    dc = 'APDC'
    wlc = function.get_wlc(dc)
    for item in wlc:
        item["dc"] = dc        

    for w in wlc:
        ip = w['managementIpAddress']
        ap_wlc[ip] = function.get_AP_in_WLC(ip)
        # print(ap_wlc[ip])
        # print(ip)
        wlc_health = function.health_wlc(dc, ip)
        # print(json.dumps(wlc_health, indent=2))
    
    for a in ap_wlc:
        print(a[1])

    return render_template("/sorfinatest.html" ,  wlcs = wlc, wlc_health = wlc_health, ap_wlc = ap_wlc)


if __name__ == '__main__':
    # index()
    app.run(debug=True, host='0.0.0.0', port=Config.port)
