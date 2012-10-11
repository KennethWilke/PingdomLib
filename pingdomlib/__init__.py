#!/usr/bin/python26

import json
import requests

server_address = 'https://api.pingdom.com'
api_version = '2.0'

class PingdomLibError(Exception):
    pass

class Pingdom(object):
    """Main connection object to interact with pingdom"""
    def __init__(self, username, password, apikey, server=server_address):
        self.username = username
        self.password = password
        self.apikey = apikey
        self.url = '%s/api/%s/' % (server, api_version)

    def checks(self):
        """Pulls all checks from pingdom"""
        response = requests.get(self.url + 'checks',
                               auth=(self.username, self.password),
                               headers={'App-Key': self.apikey})
        
        if response.status_code != 200:
            response.raise_for_status()
        
        return response.json['checks']
