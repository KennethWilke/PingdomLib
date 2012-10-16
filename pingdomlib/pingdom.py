import requests
import sys

from pingdomlib.check import PingdomCheck

server_address = 'https://api.pingdom.com'
api_version = '2.0'


class Pingdom(object):
    """Main connection object to interact with pingdom"""

    def __init__(self, username, password, apikey, pushchanges=True,
                 server=server_address):
        self.pushChanges = pushchanges
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
        elif method.upper() == 'PUT':
            response = requests.put(self.url + url, params=parameters,
                                    auth=(self.username, self.password),
                                    headers={'App-Key': self.apikey})
        elif method.upper() == 'DELETE':
            response = requests.delete(self.url + url, params=parameters,
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

        Returned structure:
        {
            'alerts' : [
                {
                    'contactname' : <String> Name of alerted contact
                    'contactid'   : <String> Identifier of alerted contact
                    'checkid'     : <String> Identifier of check
                    'time'        : <Integer> Time of alert generation. Format
                                              UNIX time
                    'via'         : <String> Alert medium ['email', 'sms',
                                                           'twitter', 'iphone',
                                                           'android']
                    'status'      : <String> Alert status ['sent', 'delivered',
                                                           'error',
                                                           'notdelivered',
                                                           'nocredits']
                    'messageshort': <String> Short description of message

                    'messagefull' : <String> Full message body
                    'sentto'      : <String> Target address, phone number, etc
                    'charged'     : <Boolean> True if your account was charged
                                              for this message
                },
                ...
            ]
        }
        """

        # Warn user about unhandled parameters
        for key in parameters:
            if key not in ['from', 'to', 'limit', 'offset', 'checkids',
                           'contactids', 'status', 'via']:
                sys.stderr.write('%s not a valid argument for actions()\n'
                                 % key)

        response = self.request('GET', 'actions', parameters)

        return response.json['actions']

    def alerts(self, **parameters):
        """A short-hand version of 'actions', returns list of alerts.
            See parameters for actions()"""

        return self.actions(**parameters)['alerts']

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

        Provide new check name, hostname and type along with any additional
            optional parameters passed as keywords

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

            * sendtotwitter -- Send alerts through Twitter
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

            * port -- Target server port
                    Type: Integer
                    Mandatory

            * stringtosend -- String to send
                    Type: String
                    Default: None

            * stringtoexpect -- String to expect in response
                    Type: String
                    Default: None

        DNS check options:

            * expectedip -- Expected IP
                    Type: String
                    Mandatory

            * nameserver -- Nameserver to check
                    Type: String
                    Mandatory

        UDP check options:

            * port -- Target server port
                    Type: Integer
                    Mandatory

            * stringtosend -- String to send
                    Type: String
                    Default: None

            * stringtoexpect -- String to expect in response
                    Type: String
                    Default: None

        SMTP check options:

            * port -- Target server port
                    Type: Integer
                    Default: 25

            * auth -- Username and password for target SMTP authentication.
                Example: user:password
                    Type: String
                    Default: None

            * stringtoexpect -- String to expect in response
                    Type: String
                    Default: None

            * encryption -- Use connection encryption
                    Type: Boolean
                    Default: False

        POP3 check options:

            * port -- Target server port
                    Type: Integer
                    Default: 110

            * stringtoexpect -- String to expect in response
                    Type: String
                    Default: None

            * encryption -- Use connection encryption
                    Type: Boolean
                    Default: False

        IMAP check options:

            * port -- Target server port
                    Type: Integer
                    Default: 143

            * stringtoexpect -- String to expect in response
                    Type: String
                    Default: None

            * encryption -- Use connection encryption
                    Type: Boolean
                    Default: False
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

    def modifyChecks(self, **kwargs):
        """Pause or change resolution for multiple checks in one bulk call.

        Parameters:

            * paused -- Check should be paused
                    Type: Boolean

            * resolution -- Check resolution time (in minutes)
                    Type: Integer [1, 5, 15, 30, 60]

            * checkids -- Comma-separated list of identifiers for checks to be
                modified. Invalid check identifiers will be ignored.
                    Type: String
        """

        # Warn user about unhandled parameters
        for key in kwargs:
            if key not in ['paused', 'resolution', 'checkids']:
                sys.stderr.write("'%s'" % key + ' is not a valid argument ' +
                                 'of newCheck()\n')

        return self.request("PUT", "checks", kwargs).json['message']

    def deleteChecks(self, checkids):
        """Deletes a list of checks, CANNOT BE REVERSED!

        Provide a comma-separated list of checkid's to delete
        """

        return self.request("DELETE", "checks",
                            {'delcheckids': checkids}).json['message']

    def credits(self):
        """Gets credits list"""

        return self.request("GET", "credits").json['credits']

    def probes(self, **kwargs):
        """Returns a list of all Pingdom probe servers

        Parameters:

            * limit -- Limits the number of returned probes to the specified
                quantity
                    Type: Integer

            * offset -- Offset for listing (requires limit).
                    Type: Integer
                    Default: 0

            * onlyactive -- Return only active probes
                    Type: Boolean
                    Default: False

            * includedeleted -- Include old probes that are no longer in use
                    Type: Boolean
                    Default: False

        Returned structure:
        [
            {
                'id'        : <Integer> Unique probe id
                'country'   : <String> Country
                'city'      : <String> City
                'name'      : <String> Name
                'active'    : <Boolean> True if probe is active
                'hostname'  : <String> DNS name
                'ip'        : <String> IP address
                'countryiso': <String> Country ISO code
            },
            ...
        ]
        """

        # Warn user about unhandled parameters
        for key in kwargs:
            if key not in ['limit', 'offset', 'onlyactive', 'includedeleted']:
                sys.stderr.write("'%s'" % key + ' is not a valid argument ' +
                                 'of probes()\n')

        return self.request("GET", "probes", kwargs).json['probes']

    def references(self):
        """Get a reference of regions, timezones and date/time/number formats
            and their identifiers.

        Returned structure:
        {
            'regions' :
            [
                {
                   'id'               : <Integer> Region identifier
                   'description'      : <String> Region description
                   'countryid'        : <Integer> Corresponding country
                                                   identifier
                   'datetimeformatid' : <Integer> Corresponding datetimeformat
                                                   identifier
                   'numberformatid'   : <Integer> Corresponding numberformat
                                                   identifer
                   'timezoneid'       : <Integer> Corresponding timezone
                                                   identifier
                },
                ...
            ],
            'timezones' :
            [
                {
                    'id'          : <Integer> Time zone identifier
                    'description' : <String> Time zone description
                },
                ...
            ],
            'datetimeformats' :
            [
                {
                    'id'          : <Integer> Date/time format identifer
                    'description' : <String> Date/time format description
                },
                ...
            ],
            'numberformats' :
            [
                {
                    'id'          : <Integer> Number format identifier
                    'description' : <String> Number format description
                },
                ...
            ],
            'countries' :
            [
                {
                    'id'  : <Integer> Country id
                    'iso' : <String> Country ISO code
                },
                ...
            ],
            'phonecodes' :
            [
                {
                    'countryid' : <Integer> Country id
                    'name'      : <String> Country name
                    'phonecode' : <String> Area phone code
                },
                ...
            ]
        }"""

        return self.request("GET", "reference").json

    def traceroute(self, host, probeid):
        """Perform a traceroute to a specified target from a specified Pingdom
            probe.

            Provide hostname to check and probeid to check from

        Returned structure:
        {
            'result'           : <String> Traceroute output
            'probeid'          : <Integer> Probe identifier
            'probedescription' : <String> Probe description
        }
        """

        response = self.request('GET', 'traceroute', {'host': host,
                                                      'probeid': probeid})
        return response.json['traceroute']

    def servertime(self):
        """Get the current time of the API server in UNIX format"""

        return self.request('GET', 'servertime').json['servertime']
