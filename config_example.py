import bcrypt

class Config:
    # credentials
    dnac = "https://10.54.201.2/dna"
    script_path = "PATH/TO/YOUR/SCRIPT/"
    username = "TACACS_USERNAME"
    password = 'TACACS_PASSWORD'
    token = ''
    port = 5004
    SECRET_KEY = 'SECRET_KEY'

    # initial values
    floor10id = ''
    floor13aid = ''

    # list of users
    users = {
        "john.doe@axa.com": {
            "email": "john.doe@axa.com",
            "name": "John Doe",
            "password": bcrypt.hashpw(b"PASSWORD", bcrypt.gensalt()),  
        }
    }
