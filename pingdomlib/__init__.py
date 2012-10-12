#!/usr/bin/python26

import sys
import requests

server_address = 'https://api.pingdom.com'
api_version = '2.0'
checktypes = ['http', 'httpcustom', 'tcp', 'ping', 'dns', 'udp', 'smtp',
              'pop3', 'imap']


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
                    Default: None

            * to -- Only include actions generated prior to this timestamp.
                Format is UNIX time.
                    Type: Integer
                    Default: None

            * limit -- Limits the number of returned results to the specified
                quantity.
                    Type: Integer (max 300)
                    Default: 100

            * offset -- Offset for listing.
                    Type: Integer
                    Default: 0

            * checkids -- Comma-separated list of check identifiers. Limit
                results to actions generated from these checks.
                    Type: String
                    Default: All

            * contactids -- Comma-separated list of contact identifiers.
                Limit results to actions sent to these contacts.
                    Type: String
                    Default: All

            * status -- Comma-separated list of statuses. Limit results to
                actions with these statuses.
                    Type: String ['sent', 'delivered', 'error',
                        'not_delivered', 'no_credits']
                    Default: All

            * via -- Comma-separated list of via mediums. Limit results to
                actions with these mediums.
                    Type: String ['email', 'sms', 'twitter', 'iphone',
                        'android']
                    Default: All
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
                    Default: 25000

            * offset -- Offset for listing (requires limit.)
                    Type: Integer
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

        check = PingdomCheck(self, {'id': checkid})
        check.getDetails()
        return check

    def newCheck(self, name, host, checktype='http', **kwargs):
        """Creates a new check with settings specified by provided parameters.

        Types available:

            * http
            * httpcustom
            * tcp
            * ping
            * dns
            * udp
            * smtp
            * pop3

        Optional parameters:

            * paused -- Check should be paused
                    Type: Boolean
                    Default: False

            * resolution -- Check resolution time (in minutes)
                    Type: Integer [1, 5, 15, 30, 60]
                    Default: 5

            * contactids -- Comma separated list of contact IDs
                    Type: String
                    Default: None

            * sendtoemail -- Send alerts as email
                    Type: Boolean
                    Default: False

            * sendtosms -- Send alerts as SMS
                    Type: Boolean
                    Default: False

            * sendtoiphone -- Send alerts to iPhone
                    Type: Boolean
                    Default: False

            * sendtoandroid -- Send alerts to Android
                    Type: Boolean
                    Default: False

            * sendnotificationwhendown -- Send notification when check is down
                the given number of times
                    Type: Integer
                    Default: 2

            * notifyagainevery -- Set how many results to wait for in between
                notices
                    Type: Integer
                    Default: 0

            * notifywhenbackup -- Notify when back up again
                    Type: Boolean
                    Default: True

        HTTP check options:

            * url -- Target path on server
                    Type: String
                    Default: /

            * encryption -- Use SSL/TLS
                    Type: Boolean
                    Default: False

            * port -- Target server port
                    Type: Integer
                    Default: 80

            * auth -- Username and password for HTTP authentication
                Example: user:password
                    Type: String
                    Default: None

            * shouldcontain -- Target site should contain this string.
                Cannot be combined with 'shouldnotcontain'
                    Type: String
                    Default: None

            * shouldnotcontain -- Target site should not contain this string.
                Cannot be combined with 'shouldcontain'
                    Type: String
                    Default: None

            * postdata -- Data that should be posted to the web page,
                for example submission data for a sign-up or login form.
                The data needs to be formatted in the same way as a web browser
                would send it to the web server
                    Type: String
                    Default: None
            * requestheader<NAME> -- Custom HTTP header, replace <NAME> with
                desired header name. Header in form: Header:Value
                    Type: String
                    Default: None

        HTTPCustom check options:

            * url -- Target path on server
                    Type: String
                    Mandatory

            * encryption -- Use SSL/TLS
                    Type: Boolean
                    Default: False

            * port -- Target server port
                    Type: Integer
                    Default: 80

            * auth -- Username and password for HTTP authentication
                Example: user:password
                    Type: String
                    Default: None

            * additionalurls -- Colon-separated list of additonal URLS with
                hostname included
                    Type: String
                    Default: None

        TCP check options:
        """

        if checktype == 'http':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['paused', 'resolution', 'contactids',
                               'sendtoemail', 'sendtosms', 'sendtotwitter',
                               'sendtoiphone', 'sendnotificationwhendown',
                               'notifyagainevery', 'notifywhenbackup',
                               'created', 'type', 'hostname', 'status',
                               'lasterrortime', 'lasttesttime', 'url',
                               'encryption', 'port', 'auth', 'shouldcontain',
                               'shouldnotcontain', 'postdata']:
                    if key.startswith('requestheader') is not True:
                        sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                         'argument of newCheck() for type ' +
                                         "'http'\n")
        elif checktype == 'httpcustom':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['paused', 'resolution', 'contactids',
                               'sendtoemail', 'sendtosms', 'sendtotwitter',
                               'sendtoiphone', 'sendnotificationwhendown',
                               'notifyagainevery', 'notifywhenbackup',
                               'created', 'type', 'hostname', 'status',
                               'lasterrortime', 'lasttesttime', 'url',
                               'encryption', 'port', 'auth', 'additionalurls']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of newCheck() for type ' +
                                     "'httpcustom'\n")
        elif checktype == 'tcp':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['paused', 'resolution', 'contactids',
                               'sendtoemail', 'sendtosms', 'sendtotwitter',
                               'sendtoiphone', 'sendnotificationwhendown',
                               'notifyagainevery', 'notifywhenbackup',
                               'created', 'type', 'hostname', 'status',
                               'lasterrortime', 'lasttesttime', 'port',
                               'stringtosend', 'stringtoexpect']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of newCheck() for type ' +
                                     "'tcp'\n")
        elif checktype == 'ping':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['paused', 'resolution', 'contactids',
                               'sendtoemail', 'sendtosms', 'sendtotwitter',
                               'sendtoiphone', 'sendnotificationwhendown',
                               'notifyagainevery', 'notifywhenbackup',
                               'created', 'type', 'hostname', 'status',
                               'lasterrortime', 'lasttesttime']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of newCheck() for type ' +
                                     "'ping'\n")
        elif checktype == 'dns':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['paused', 'resolution', 'contactids',
                               'sendtoemail', 'sendtosms', 'sendtotwitter',
                               'sendtoiphone', 'sendnotificationwhendown',
                               'notifyagainevery', 'notifywhenbackup',
                               'created', 'type', 'hostname', 'status',
                               'lasterrortime', 'lasttesttime', 'expectedip',
                               'nameserver']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of newCheck() for type ' +
                                     "'dns'\n")
        elif checktype == 'udp':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['paused', 'resolution', 'contactids',
                               'sendtoemail', 'sendtosms', 'sendtotwitter',
                               'sendtoiphone', 'sendnotificationwhendown',
                               'notifyagainevery', 'notifywhenbackup',
                               'created', 'type', 'hostname', 'status',
                               'lasterrortime', 'lasttesttime', 'port',
                               'stringtosend', 'stringtoexpect']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of newCheck() for type ' +
                                     "'udp'\n")
        elif checktype == 'smtp':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['paused', 'resolution', 'contactids',
                               'sendtoemail', 'sendtosms', 'sendtotwitter',
                               'sendtoiphone', 'sendnotificationwhendown',
                               'notifyagainevery', 'notifywhenbackup',
                               'created', 'type', 'hostname', 'status',
                               'lasterrortime', 'lasttesttime', 'port', 'auth',
                               'stringtoexpect', 'encryption']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of newCheck() for type ' +
                                     "'smtp'\n")
        elif checktype == 'pop3':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['paused', 'resolution', 'contactids',
                               'sendtoemail', 'sendtosms', 'sendtotwitter',
                               'sendtoiphone', 'sendnotificationwhendown',
                               'notifyagainevery', 'notifywhenbackup',
                               'created', 'type', 'hostname', 'status',
                               'lasterrortime', 'lasttesttime', 'port',
                               'stringtoexpect', 'encryption']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of newCheck() for type ' +
                                     "'pop3'\n")
        elif checktype == 'imap':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['paused', 'resolution', 'contactids',
                               'sendtoemail', 'sendtosms', 'sendtotwitter',
                               'sendtoiphone', 'sendnotificationwhendown',
                               'notifyagainevery', 'notifywhenbackup',
                               'created', 'type', 'hostname', 'status',
                               'lasterrortime', 'lasttesttime', 'port',
                               'stringtoexpect', 'encryption']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of newCheck() for type ' +
                                     "'imap'\n")
        else:
            raise Exception("Invalid checktype in newCheck()")

        parameters = {'name': name, 'host': host, 'type': checktype}
        for key, value in kwargs.iteritems():
            parameters[key] = value

        checkinfo = self.request("POST", 'checks', parameters)
        return self.getCheck(checkinfo.json['check']['id'])


class PingdomCheck(object):
    """Class representing a check in pingdom"""

    def __init__(self, instantiator, checkinfo=dict()):
        self.pingdom = instantiator
        self.addDetails(checkinfo)

    def __getattr__(self, attr):
        # Pull variables from pingdom if unset
        if attr in ['id', 'name', 'resolution', 'sendtoemail', 'sendtosms',
                    'sendtotwitter', 'sendtoiphone',
                    'sendnotificationwhendown', 'notifyagainevery',
                    'notifywhenbackup', 'created', 'type', 'hostname',
                    'status', 'lasterrortime', 'lasttesttime']:
            self.getDetails()
            return getattr(self, attr)
        else:
            raise AttributeError("'PingdomCheck' object has no attribute '%s'"
                                 % attr)

    def getAnalyses(self, **parameters):
        """Returns a list of the latest root cause analysis results for a
            specified check.

        Optional Parameters:

            * limit -- Limits the number of returned results to the
                specified quantity.
                    Type: Integer
                    Default: 100

            * offset -- Offset for listing. (Requires limit.)
                    Type: Integer
                    Default: 0

            * from -- Return only results with timestamp of first test greater
                or equal to this value. Format is UNIX timestamp.
                    Type: Integer
                    Default: 0

            * to -- Return only results with timestamp of first test less or
                equal to this value. Format is UNIX timestamp.
                    Type: Integer
                    Default: Current Time
        """

        # Warn user about unhandled parameters
        for key in parameters:
            if key not in ['limit', 'offset', 'from', 'to']:
                sys.stderr.write('%s not a valid argument for analysis()\n'
                                 % key)

        response = self.pingdom.request('GET', 'analysis/%s' % self.id,
                                        parameters)

        return [PingdomAnalysis(self, x) for x in response.json['analysis']]

    def addDetails(self, checkinfo):
        # Auto-load instance attributes from passed in dictionary
        for key in checkinfo:
            if key == 'type':
                if checkinfo[key] in checktypes:
                    self.type = checkinfo[key]
                else:
                    # Take key from type dict, convert to string for type
                    self.type = checkinfo[key].iterkeys().next()

                    # Take value from type dict, store to member of new attrib
                    setattr(self, self.type,
                            checkinfo[key].itervalues().next())
            else:
                # Store other key value pairs as attributes
                setattr(self, key, checkinfo[key])

    def getDetails(self):
        response = self.pingdom.request('GET', 'checks/%s' % self.id)
        self.addDetails(response.json['check'])
        return response.json['check']


class PingdomAnalysis(object):
    """Class representing a root cause analysis"""

    def __init__(self, instantiator, analysis):
        self.pingdom = instantiator.pingdom
        self.checkid = instantiator.id
        self.id = analysis['id']
        self.timefirsttest = analysis['timefirsttest']
        self.timeconfirmtest = analysis['timeconfirmtest']

    def getDetails(self):
        response = self.pingdom.request('GET', 'analysis/%s/%s' %
                                        (self.checkid, self.id))
        return response.text
