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
    clients = function.get_clients()
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
    access_points = function.get_ap()
    print(len(access_points))
    # print(access_points)
    return render_template("access-points.html", access_points=access_points)

@app.route('/ap-detail/<ap_mac>', methods=['POST', 'GET'])
def ap_detail(ap_mac):
    ap = function.get_ap_detail(ap_mac)
    wlc = function.get_devName(ap.get("connectedWlcUuid"))
    ap_details = function.get_dev_details(ap.get("nwDeviceId"))
    radio = function.get_ap_radio(ap.get("nwDeviceName"))
    return render_template('ap-detail.html', ap=ap, wlc=wlc, ap_details=ap_details, radio=radio)

@app.route('/network-devices', methods=['POST', 'GET'])
def devices():
    devices = function.get_devices()
    return render_template("network-devices.html", devices=devices)

if __name__ == '__main__':
    # index()
    app.run(debug=True, host='0.0.0.0', port=Config.port)