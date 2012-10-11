#!/usr/bin/python26

import sys
import requests

server_address = 'https://api.pingdom.com'
api_version = '2.0'


class Pingdom(object):
    """Main connection object to interact with pingdom"""

    def __init__(self, username, password, apikey, server=server_address):
        self.username = username
        self.password = password
        self.apikey = apikey
        self.url = '%s/api/%s/' % (server, api_version)
        self.shortlimit = ''
        self.longlimit = ''

    def request(self, method, url, parameters=None):
        """Requests wrapper function"""

        # Method selection handling
        if method.upper() == 'GET':
            response = requests.get(self.url + url, params=parameters,
                                    auth=(self.username, self.password),
                                    headers={'App-Key': self.apikey})
        elif method.upper() == 'POST':
            response = requests.post(self.url + url, params=parameters,
                                     auth=(self.username, self.password),
                                     headers={'App-Key': self.apikey})
        else:
            raise Exception("Invalid method in pingdom request")

        # Verify OK response
        if response.status_code != 200:
            response.raise_for_status()

        # Store pingdom api limits
        self.shortlimit = response.headers['Req-Limit-Short']
        self.longlimit = response.headers['Req-Limit-Long']

        return response

    def actions(self, **parameters):
        """Returns a list of actions (alerts) that have been generated for
            your account.

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

        # Warn user about unhandled parameters
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

        # Warn user about unhandled parameters
        for key in parameters:
            if key not in ['limit', 'offset']:
                sys.stderr.write('%s not a valid argument for getChecks()\n'
                                 % key)

        response = self.request('GET', 'checks', parameters)

        return [PingdomCheck(self, x) for x in response.json['checks']]

    def getCheck(self, checkid):
        """Returns a detailed description of a specified check."""

        response = self.request('GET', 'checks/%s' % checkid)

        return PingdomCheck(self, response.json['check'])


class PingdomCheck(object):
    """Class representing a check in pingdom"""

    def __init__(self, instantiator, checkinfo=dict()):
        self.pingdom = instantiator
        # Auto-load instance attributes from passed in dictionary
        for key in checkinfo:
            if key == 'type':
                # Take key from type dict, convert to string for type attribute
                self.type = checkinfo[key].iterkeys().next()
                # Take value from type dict, store to member of new attribute
                setattr(self, self.type, checkinfo[key].itervalues().next())
            else:
                # Store other key value pairs as attributes
                setattr(self, key, checkinfo[key])

    def analysis(self, **parameters):
        """Returns a list of the latest root cause analysis results for a
            specified check."""
        response = self.pingdom.request('GET', 'analysis/%s' % self.id,
                                        parameters)

        return response.json['analysis']
