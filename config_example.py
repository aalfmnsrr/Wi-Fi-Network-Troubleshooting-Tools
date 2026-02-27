import bcrypt
from datetime import datetime

class Config:
    # datetime
    today = datetime.now()
    year = today.strftime("%Y")
    abbmonth = today.strftime("%b")
    month = today.strftime("%m")
    day = today.strftime("%d")

    # paths
    dnac = "https://dnac.example.local/dna"
    script_path = "PATH/TO/YOUR/SCRIPT/"
    inventory_path = f"{script_path}/inventory/{year}/{abbmonth}/{day}"
    ap_path = f"{inventory_path}/APs/ap.json"
    wlc_path = f"{inventory_path}/WLCs/wlc.json"
    switch_path = f"{inventory_path}/Switches/switches.json"
    dashboard_path = f"{inventory_path}/Dashboard/dashboard.json"

    # credentials
    username = ''
    password = ''
    token = ''
    port = ''
    SECRET_KEY = ''

    # initial values
    floor_id =[]

    # list of users
    users = {
        "john.doe@axa.com": {
            "email": "john.doe@axa.com",
            "name": "John Doe",
            "password": bcrypt.hashpw(b"PASSWORD", bcrypt.gensalt()),  
        }
    }
