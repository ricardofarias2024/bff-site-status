# import time
# import schedule
# import os
# import requests
import json
# import pdb
# import threading
# from datetime import datetime
from flask import Flask, send_file
from pyzabbix.api import ZabbixAPI
from dotenv import dotenv_values
from flask_cors import CORS

# Load environment variables from .env file
env_vars = dotenv_values()

URL = "https://zabbix.devops.rentcars.com/api_jsonrpc.php"
USERNAME = env_vars.get("USERNAME")
PASSWORD = env_vars.get("PASSWORD")

app = Flask(__name__)
CORS(app)

@app.route('/ping')
def index():
    response = {
        "message": "Pong!"
    }
    return json.dumps(response)

@app.route('/geteventzabbix')
def getEventZabbix():
    zapi = ZabbixAPI(URL, timeout=180)
    zapi.login(USERNAME, PASSWORD)
    # Get all events
    events = zapi.event.get({
        "output": ["eventid", "objectid", "clock", "value", "acknowledged"],
        "selectHosts": ["hostid", "host"],
        "selectRelatedObject": ["triggerid", "description", "priority", "value"]
    })
    zapi.logout()
    return json.dumps(events)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090)
    # thread_scheduler = threading.Thread(target=scheduler)
    # thread_scheduler.start()

    # thread_app = threading.Thread(target=init_app)
    # thread_app.start()

    # thread_scheduler.join()
    # thread_app.join()