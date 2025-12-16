from flask import Flask, render_template, render_template_string
from config import Config
import function

app = Flask(__name__, template_folder='templates/docs')

@app.route('/', methods=['POST', 'GET'])
def dashboard():
    function.get_devices()
    return render_template("dashboard.html")

@app.route('/clients', methods=['POST', 'GET'])
def clients():
    function.get_clients()
    clients = Config.clients
    # print(clients)
    # print(len(clients))
    return render_template("clients.html", clients=clients)

@app.route('/client-detail/<client_mac>', methods=['POST', 'GET'])
def device_detail(client_mac):
    client = function.get_client_enrichment_detail(client_mac)
    connectedAP = client["connectedDevice"][0].get("deviceDetails")
    client = client["userDetails"]
    return render_template('client-detail.html', client=client, connectedAP=connectedAP)

@app.route('/access-points', methods=["POST", "GET"])
def access_points():
    function.get_ap()
    access_points = Config.access_points
    # print(access_points)
    return render_template("access-points.html", access_points=access_points)

@app.route('/ap-detail/<ap_mac>', methods=['POST', 'GET'])
def ap_detail(ap_mac):
    ap = function.get_ap_detail(ap_mac)
    return render_template('ap-detail.html', ap=ap)

@app.route('/network-devices', methods=['POST', 'GET'])
def devices():
    function.get_devices()
    return render_template("network-devices.html", devices=Config.devices)

@app.route('/wlc/id=<wlc_id>', methods=['POST', 'GET'])
def wlc_ssid(wlc_id):
    # function.get_devices()

    # id = function.wlc_id(function.get_wlc()[1])
    ssids = function.get_ssid(wlc_id)

    int = function.wlc_int(wlc_id)
    wlc = Config.wlc

    for w in wlc:
        if wlc_id == w.get('id'):
            hostname = w.get('hostname')

    # print(hostname)
  
    return render_template("/wlc/wlc_ssid.html", hostname=hostname, ssids = ssids, int = int)

@app.route('/wlc', methods=['POST', 'GET'])
def wlc():
    
    function.get_wlc()
    ap_wlc = {}
    wlc = Config.wlc

    for w in Config.wlc:
        ip = w['managementIpAddress']
        ap_wlc[ip] = function.get_AP_in_WLC(ip)
        wlc_health = function.health_wlc(ip)

    return render_template("/wlc/wlc_dashboard.html",  wlcs = wlc, wlc_health = wlc_health, ap_wlc = ap_wlc)



if __name__ == '__main__':
    # index()
    app.run(debug=True, host='0.0.0.0', port=5002)



