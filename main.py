from flask import Flask, render_template, render_template_string, request
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

# Alif
@app.route('/switches', methods=['POST', 'GET'])
def switches():
    role_filter = request.args.get('role')
    function.get_switches(role = role_filter)
    return render_template("switches.html", devices=Config.devices)

@app.route('/switches/<device_id>', methods=['GET'])
def switch_detail(device_id):
    try:
        device = function.get_switch_details(device_id)
        
    except Exception as e:
        abort(500, description = f"Failed to retrieve device details: {e}")
    
    if not device:
        abort(404, description = "Switch device not found")

    device_mac = device.get('macAddress')
    
    sw_health = None
    if device_mac:
        try:
            sw_health = function.get_switch_health(device_mac)
        except Exception:
            sw_health = None
    
    vlan_count = None
    try:
        vlans = function.get_vlan(device_id)
        vlan_count = len(vlans)
    except Exception as e:
        print("VLAN count error:", e)

    return render_template("sw-details.html", device=device, sw_health=sw_health, vlan_count=vlan_count)

@app.route('/switches/<device_id>/vlans', methods=['GET'])
def switch_vlans(device_id):
    try:
        device = function.get_switch_details(device_id)
        if not device:
            abort(404, description="Switch device not found")
    except Exception as e:
        abort(500, description=f"Failed to retriece device details: {e}")

    vlans = None
    try:
        vlans = function.get_vlan(device_id)
    except Exception as e:
        abort(500, description=f"Failed to retrieve VLANS: {e}")

    return render_template("sw-vlan.html", device=device, vlans=vlans)

if __name__ == '__main__':
    # index()
    app.run(debug=True, host='0.0.0.0', port=Config.port)