import bcrypt

class Config:
    # credentials
    dnac = "https://10.54.201.2/dna"
    script_path = "PATH/TO/YOUR/SCRIPT/"
    username = "TACACS_USERNAME"
    password = 'TACACS_PASSWORD'
    token = ''
    port = 5004

    # initial values
    floor10id = '10TH_FLOOR_ID'
    floor13aid = '13A_FLOOR_ID'

    # list of users
    users = {
        "john.doe@axa.com": {
            "email": "john.doe@axa.com",
            "name": "John Doe",
            "password": bcrypt.hashpw(b"PASSWORD", bcrypt.gensalt()),  
        }
    }