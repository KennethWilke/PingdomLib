#!/usr/bin/python26

import sys
import requests

server_address = 'https://api.pingdom.com'
api_version = '2.0'


class PingdomLibError(Exception):
    """Exception wrapper"""
    pass


class Pingdom(object):
    """Main connection object to interact with pingdom"""

    def __init__(self, username, password, apikey, server=server_address):
        self.username = username
        self.password = password
        self.apikey = apikey
        self.url = '%s/api/%s/' % (server, api_version)

    def request(self, method, url, parameters=None):
        """Generic request method"""
        if method.upper() == 'GET':
            response = requests.get(self.url + url, params=parameters,
                                    auth=(self.username, self.password),
                                    headers={'App-Key': self.apikey})
        elif method.upper() == 'POST':
            response = requests.post(self.url + url, params=parameters,
                                     auth=(self.username, self.password),
                                     headers={'App-Key': self.apikey})
        else:
            raise PingdomLibError("Invalid method")

        if response.status_code != 200:
            response.raise_for_status()

        return response

    def actions(self, **parameters):
        """Returns a list of actions generated for your account.

        Optional Parameters:

            * from -- Only include actions generated later than this timestamp.
                Format is UNIX time.
                    Type: Integer
                    Mandatory: No
                    Default: None

            * to -- Only include actions generated prior to this timestamp.
                Format is UNIX time.
                    Type: Integer
                    Mandatory: No
                    Default: None

            * limit -- Limits the number of returned results to the specified
                quantity.
                    Type: Integer (max 300)
                    Mandatory: No
                    Default: 100

            * offset -- Offset for listing.
                    Type: Integer
                    Mandatory: No
                    Default: 0

            * checkids -- Comma-separated list of check identifiers. Limit
                results to actions generated from these checks.
                    Type: String
                    Mandatory: No
                    Default: None

            * contactids -- Comma-separated list of contact identifiers.
                Limit results to actions sent to these contacts.
                    Type: String
                    Mandatory: No
                    Default: None

            * status -- Comma-separated list of statuses. Limit results to
                actions with these statuses.
                    Type: String ['sent', 'delivered', 'error',
                        'not_delivered', 'no_credits']
                    Mandatory: No
                    Default: None

            * via -- Comma-separated list of via mediums. Limit results to
                actions with these mediums.
                    Type: String ['email', 'sms', 'twitter', 'iphone',
                        'android']
                    Mandatory: No
                    Default: None
        """

        for key in parameters:
            if key not in ['from', 'to', 'limit', 'offset', 'checkids',
                           'contactids', 'status', 'via']:
                sys.stderr.write('%s not a valid argument for actions()\n'
                                 % key)

        response = self.request('GET', 'actions', parameters)

        return response.json['actions']

    def getChecks(self, **parameters):
        """Pulls all checks from pingdom

        Optional Parameters:

            * limit -- Limits the number of returned probes to the
                specified quantity.
                    Type: Integer (max 25000)
                    Mandatory: No
                    Default: 25000

            * offset -- Offset for listing (requires limit.)
                    Type: Integer
                    Mandatory: No
                    Default: 0
        """

        for key in parameters:
            if key not in ['limit', 'offset']:
                sys.stderr.write('%s not a valid argument for getChecks()\n'
                                 % key)

        response = self.request('GET', 'checks', parameters)

        return response.json['checks']
