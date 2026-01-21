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
    dnac = "https://10.54.201.2/dna"
    script_path = "PATH/TO/YOUR/SCRIPT/"
    inventory_path = f"{script_path}/inventory/{year}/{abbmonth}/{day}"
    ap_path = f"{inventory_path}/APs"
    wlc_path = f"{inventory_path}/WLCs"
    switch_path = f"{inventory_path}/Switches"

    # credentials
    username = "TACACS_USERNAME"
    password = 'TACACS_PASSWORD'
    token = ''
    port = 5004
    SECRET_KEY = 'SECRET_KEY'

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
