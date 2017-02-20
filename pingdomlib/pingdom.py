import requests
import sys

from pingdomlib.check import PingdomCheck
from pingdomlib.contact import PingdomContact
from pingdomlib.reports import PingdomEmailReport, PingdomSharedReport

server_address = 'https://api.pingdom.com'
api_version = '2.0'


class Pingdom(object):
    """Main connection object to interact with pingdom

    Attributes:

        * pushChanges -- This boolean controls if changes are automatically
            pushed to pingdom

        * shortlimit -- String containing short api rate limit details

        * longlimit -- String containing long api rate limit details
    """

    def __init__(self, username, password, apikey, accountemail=None,
                 pushchanges=True, server=server_address):
        self.pushChanges = pushchanges
        self.username = username
        self.password = password
        self.apikey = apikey
        self.accountemail = accountemail
        self.url = '%s/api/%s/' % (server, api_version)
        self.shortlimit = ''
        self.longlimit = ''

    @staticmethod
    def _serializeBooleans(params):
        """"Convert all booleans to lowercase strings"""
        serialized = {}
        for name, value in params.items():
            if value is True:
                value = 'true'
            elif value is False:
                value = 'false'
            serialized[name] = value
        return serialized

        for k, v in params.items():
            if isinstance(v, bool):
                params[k] = str(v).lower()

    def request(self, method, url, parameters=dict()):
        """Requests wrapper function"""

        # The requests library uses urllib, which serializes to "True"/"False" while Pingdom requires lowercase
        parameters = self._serializeBooleans(parameters)

        headers = {'App-Key': self.apikey}
        if self.accountemail:
            headers.update({'Account-Email': self.accountemail})

        # Method selection handling
        if method.upper() == 'GET':
            response = requests.get(self.url + url, params=parameters,
                                    auth=(self.username, self.password),
                                    headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(self.url + url, data=parameters,
                                     auth=(self.username, self.password),
                                     headers=headers)
        elif method.upper() == 'PUT':
            response = requests.put(self.url + url, data=parameters,
                                    auth=(self.username, self.password),
                                    headers=headers)
        elif method.upper() == 'DELETE':
            response = requests.delete(self.url + url, params=parameters,
                                       auth=(self.username, self.password),
                                       headers=headers)
        else:
            raise Exception("Invalid method in pingdom request")

        # Store pingdom api limits
        self.shortlimit = response.headers.get(
            'Req-Limit-Short',
            self.shortlimit)
        self.longlimit = response.headers.get(
            'Req-Limit-Long',
            self.longlimit)

        # Verify OK response
        if response.status_code != 200:
            sys.stderr.write('ERROR from %s: %d' % (response.url,
                                                    response.status_code))
            sys.stderr.write('Returned data: %s\n' % response.json())
            response.raise_for_status()

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

        return response.json()['actions']

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

            * tags -- Filter listing by tag/s
                    Type: String
                    Default: None

        """

        # Warn user about unhandled parameters
        for key in parameters:
            if key not in ['limit', 'offset', 'tags']:
                sys.stderr.write('%s not a valid argument for getChecks()\n'
                                 % key)

        response = self.request('GET', 'checks', parameters)

        return [PingdomCheck(self, x) for x in response.json()['checks']]

    def getCheck(self, checkid):
        """Returns a detailed description of a specified check."""

        check = PingdomCheck(self, {'id': checkid})
        check.getDetails()
        return check

    def getResults(self, checkid):
        """ Returns detailed results for a specified check id."""
        response = self.request('GET','results/%s' % checkid)
        return response.json()

    def newCheck(self, name, host, checktype='http', **kwargs):
        """Creates a new check with settings specified by provided parameters.

        Provide new check name, hostname and type along with any additional
            optional parameters passed as keywords. Returns new PingdomCheck
            instance

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

            * use_legacy_notifications -- Use the old notifications instead of
                BeepManager
                    Type: Boolean
                    Default: False

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
                if key not in ['alert_policy', 'autoresolve', 'paused', 'resolution', 'contactids',
                               'sendtoemail', 'sendtosms', 'sendtotwitter',
                               'sendtoiphone', 'sendtoandroid',
                               'sendnotificationwhendown', 'notifyagainevery',
                               'notifywhenbackup', 'type', 'hostname', 'url',
                               'encryption', 'port', 'auth', 'shouldcontain',
                               'shouldnotcontain', 'postdata',
                               'use_legacy_notifications']:
                    if key.startswith('requestheader') is not True:
                        sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                         'argument of newCheck() for type ' +
                                         "'http'\n")
        elif checktype == 'httpcustom':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['paused', 'resolution', 'contactids',
                               'sendtoemail', 'sendtosms', 'sendtotwitter',
                               'sendtoiphone', 'sendtoandroid',
                               'sendnotificationwhendown', 'notifyagainevery',
                               'notifywhenbackup', 'type', 'hostname', 'url',
                               'encryption', 'port', 'auth', 'additionalurls',
                               'use_legacy_notifications']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of newCheck() for type ' +
                                     "'httpcustom'\n")
        elif checktype == 'tcp':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['alert_policy', 'autoresolve', 'paused', 'resolution', 'contactids',
                               'sendtoemail', 'sendtosms', 'sendtotwitter',
                               'sendtoiphone', 'sendtoandroid',
                               'sendnotificationwhendown', 'notifyagainevery',
                               'notifywhenbackup', 'type', 'hostname', 'port',
                               'stringtosend', 'stringtoexpect',
                               'use_legacy_notifications']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of newCheck() for type ' +
                                     "'tcp'\n")
        elif checktype == 'ping':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['paused', 'resolution', 'contactids',
                               'sendtoemail', 'sendtosms', 'sendtotwitter',
                               'sendtoiphone', 'sendtoandroid',
                               'sendnotificationwhendown', 'notifyagainevery',
                               'notifywhenbackup', 'type', 'hostname',
                               'use_legacy_notifications']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of newCheck() for type ' +
                                     "'ping'\n")
        elif checktype == 'dns':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['paused', 'resolution', 'contactids',
                               'sendtoemail', 'sendtosms', 'sendtotwitter',
                               'sendtoiphone', 'sendtoandroid',
                               'sendnotificationwhendown', 'notifyagainevery',
                               'notifywhenbackup', 'type', 'hostname',
                               'expectedip', 'nameserver',
                               'use_legacy_notifications']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of newCheck() for type ' +
                                     "'dns'\n")
        elif checktype == 'udp':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['paused', 'resolution', 'contactids',
                               'sendtoemail', 'sendtosms', 'sendtotwitter',
                               'sendtoiphone', 'sendtoandroid',
                               'sendnotificationwhendown', 'notifyagainevery',
                               'notifywhenbackup', 'type', 'hostname', 'port',
                               'stringtosend', 'stringtoexpect',
                               'use_legacy_notifications']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of newCheck() for type ' +
                                     "'udp'\n")
        elif checktype == 'smtp':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['paused', 'resolution', 'contactids',
                               'sendtoemail', 'sendtosms', 'sendtotwitter',
                               'sendtoiphone', 'sendtoandroid',
                               'sendnotificationwhendown', 'notifyagainevery',
                               'notifywhenbackup', 'type', 'hostname', 'port',
                               'auth', 'stringtoexpect', 'encryption',
                               'use_legacy_notifications']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of newCheck() for type ' +
                                     "'smtp'\n")
        elif checktype == 'pop3':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['paused', 'resolution', 'contactids',
                               'sendtoemail', 'sendtosms', 'sendtotwitter',
                               'sendtoiphone', 'sendtoandroid',
                               'sendnotificationwhendown', 'notifyagainevery',
                               'notifywhenbackup', 'type', 'hostname', 'port',
                               'stringtoexpect', 'encryption',
                               'use_legacy_notifications']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of newCheck() for type ' +
                                     "'pop3'\n")
        elif checktype == 'imap':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['paused', 'resolution', 'contactids',
                               'sendtoemail', 'sendtosms', 'sendtotwitter',
                               'sendtoiphone', 'sendtoandroid',
                               'sendnotificationwhendown', 'notifyagainevery',
                               'notifywhenbackup', 'type', 'hostname', 'port',
                               'stringtoexpect', 'encryption',
                               'use_legacy_notifications']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of newCheck() for type ' +
                                     "'imap'\n")
        else:
            raise Exception("Invalid checktype in newCheck()")

        parameters = {'name': name, 'host': host, 'type': checktype}
        for key, value in kwargs.iteritems():
            parameters[key] = value

        checkinfo = self.request("POST", 'checks', parameters)
        return self.getCheck(checkinfo.json()['check']['id'])

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

        return self.request("PUT", "checks", kwargs).json()['message']

    def deleteChecks(self, checkids):
        """Deletes a list of checks, CANNOT BE REVERSED!

        Provide a comma-separated list of checkid's to delete
        """

        return self.request("DELETE", "checks",
                            {'delcheckids': checkids}).json()['message']

    def credits(self):
        """Gets credits list"""

        return self.request("GET", "credits").json()['credits']

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

        return self.request("GET", "probes", kwargs).json()['probes']

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

        return self.request("GET", "reference").json()

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
        return response.json()['traceroute']

    def servertime(self):
        """Get the current time of the API server in UNIX format"""

        return self.request('GET', 'servertime').json()['servertime']

    def getContacts(self, **kwargs):
        """Returns a list of all contacts.

        Optional Parameters:

            * limit -- Limits the number of returned contacts to the specified
                quantity.
                    Type: Integer
                    Default: 100

            * offset -- Offset for listing (requires limit.)
                    Type: Integer
                    Default: 0

        Returned structure:
        [
            'id'                 : <Integer> Contact identifier
            'name'               : <String> Contact name
            'email'              : <String> Contact email
            'cellphone'          : <String> Contact telephone
            'countryiso'         : <String> Cellphone country ISO code
            'defaultsmsprovider' : <String> Default SMS provider
            'directtwitter'      : <Boolean> Send Tweets as direct messages
            'twitteruser'        : <String> Twitter username
            'paused'             : <Boolean> True if contact is pasued
            'iphonetokens'       : <String list> iPhone tokens
            'androidtokens'      : <String list> android tokens
        ]
        """

        # Warn user about unhandled parameters
        for key in kwargs:
            if key not in ['limit', 'offset']:
                sys.stderr.write("'%s'" % key + ' is not a valid argument ' +
                                 'of getContacts()\n')

        return [PingdomContact(self, x) for x in
                self.request("GET", "notification_contacts", kwargs).json()['contacts']]

    def newContact(self, name, **kwargs):
        """Create a new contact.

        Provide new contact name and any optional arguments. Returns new
            PingdomContact instance

        Optional Parameters:

            * email -- Contact email address
                    Type: String

            * cellphone -- Cellphone number, without the country code part. In
                some countries you are supposed to exclude leading zeroes.
                (Requires countrycode and countryiso)
                    Type: String

            * countrycode -- Cellphone country code (Requires cellphone and
                countryiso)
                    Type: String

            * countryiso -- Cellphone country ISO code. For example: US (USA),
                GB (Britain) or SE (Sweden) (Requires cellphone and
                countrycode)
                    Type: String

            * defaultsmsprovider -- Default SMS provider
                    Type: String ['clickatell', 'bulksms', 'esendex',
                                  'cellsynt']

            * directtwitter -- Send tweets as direct messages
                    Type: Boolean
                    Default: True

            * twitteruser -- Twitter user
                    Type: String
        """

        # Warn user about unhandled parameters
        for key in kwargs:
            if key not in ['email', 'cellphone', 'countrycode', 'countryiso',
                           'defaultsmsprovider', 'directtwitter',
                           'twitteruser']:
                sys.stderr.write("'%s'" % key + ' is not a valid argument ' +
                                 'of newContact()\n')

        kwargs['name'] = name
        contactinfo = self.request("POST", "notification_contacts",
                                   kwargs).json()['contact']

        return PingdomContact(self, contactinfo)

    def modifyContacts(self, contactids, paused):
        """Modifies a list of contacts.

        Provide comma separated list of contact ids and desired paused state

        Returns status message
        """

        response = self.request("PUT", "notification_contacts", {'contactids': contactids,
                                                    'paused': paused})
        return response.json()['message']

    def deleteContacts(self, contactids):
        """Deletes a list of contacts. CANNOT BE REVERSED!

        Provide a comma-separated list of contactid's to delete

        Returns status message
        """

        return self.request("DELETE", "notification_contacts",
                            {'delcheckids': contactids}).json()['message']

    def singleTest(self, host, checktype, **kwargs):
        """Performs a single test using a specified Pingdom probe against a
            specified target. Please note that this method is meant to be used
            sparingly, not to set up your own monitoring solution.

        Provide hostname and check type, followed by any optional arguments.

        Types available:

            * http
            * httpcustom
            * tcp
            * ping
            * dns
            * udp
            * smtp
            * pop3

        Optional arguments:

            * probeid -- Probe to use for check
                    Type: Integer
                    Default: A random probe

        See newCheck() docstring for type-specific arguments

        Returned structure:
        {
            'status'         : <String> Test result status ['up, 'down']
            'responsetime'   : <Integer> Response time in milliseconds
            'statusdesc'     : <String> Short status description
            'statusdesclong' : <String> Long status description
            'probeid'        : <Integer> Probe identifier
            'probedesc'      : <String> Probe description
        }
        """

        if checktype == 'http':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['probeid', 'url',
                               'encryption', 'port', 'auth', 'shouldcontain',
                               'shouldnotcontain', 'postdata']:
                    if key.startswith('requestheader') is not True:
                        sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                         'argument of singleTest() for type ' +
                                         "'http'\n")
        elif checktype == 'httpcustom':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['probeid', 'url',
                               'encryption', 'port', 'auth', 'additionalurls']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of singleTest() for type ' +
                                     "'httpcustom'\n")
        elif checktype == 'tcp':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['probeid', 'port',
                               'stringtosend', 'stringtoexpect']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of singleTest() for type ' +
                                     "'tcp'\n")
        elif checktype == 'ping':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['probeid']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of singleTest() for type ' +
                                     "'ping'\n")
        elif checktype == 'dns':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['probeid', 'expectedip',
                               'nameserver']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of singleTest() for type ' +
                                     "'dns'\n")
        elif checktype == 'udp':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['probeid', 'port',
                               'stringtosend', 'stringtoexpect']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of singleTest() for type ' +
                                     "'udp'\n")
        elif checktype == 'smtp':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['probeid', 'port', 'auth',
                               'stringtoexpect', 'encryption']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of singleTest() for type ' +
                                     "'smtp'\n")
        elif checktype == 'pop3':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['probeid', 'port',
                               'stringtoexpect', 'encryption']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of singleTest() for type ' +
                                     "'pop3'\n")
        elif checktype == 'imap':
            # Warn user about unhandled parameters
            for key in kwargs:
                if key not in ['probeid', 'port',
                               'stringtoexpect', 'encryption']:
                    sys.stderr.write("'%s'" % key + ' is not a valid ' +
                                     'argument of singleTest() for type ' +
                                     "'imap'\n")
        else:
            raise Exception("Invalid checktype in singleTest()")

        parameters = {'host': host, 'type': checktype}
        for key, value in kwargs.iteritems():
            parameters[key] = value

        checkinfo = self.request('GET', "single", parameters)

        return checkinfo.json()['result']

    def getSettings(self):
        """Returns all account-specific settings.

        Returned structure:
        {
            'firstname'           : <String> First name
            'lastname'            : <String> Last name
            'company'             : <String> Company
            'email'               : <String> Email
            'phone'               : <String> Phone
            'phonecountryiso'     : <String> Phone country ISO code
            'cellphone'           : <String> Cellphone
            'cellphonecountryiso' : <String> Cellphone country ISO code
            'address'             : <String> Address line 1
            'address2'            : <String> Address line 2
            'zip'                 : <String> Zip, postal code or equivalent
            'location'            : <String> City / location
            'state'               : <String> State or equivalent
            'autologout'          : <Boolean> Enable auto-logout
            'country'             :
            {
                'name'      : <String> Country name
                'iso'       : <String> Country ISO-code
                'countryid' : <Integer> Country identifier
            }
            'vatcode'             : <String> For certain EU countries, VAT-code
            'region'              : <String> Region
            'regionid'            : <Integer> Region identifier, see reference
            'accountcreated'      : <Integer> Account creation timestamp
            'timezone'            :
            {
                'id'          : <String> Timezone name
                'description' : <String> Timezone description
                'timezoneid'  : <Integer> Timezone identifier
            }
            'dateformat'          : <String> Date format
            'timeformat'          : <String> Time format
            'datetimeformatid'    : <Integer> Date/time format identifier
            'numberformat'        : <String> Number format
            'numberformatexample' : <String> Example of number presentation
            'numberformatid'      : <Integer> Number format identifier
            'publicreportscode'   : <String> URL code
            'settingssaved'       : <Boolean> True if user has saved initial
                                     settings in control panel
        }
        """

        return self.request('GET', 'settings').json()['settings']

    def modifySettings(self, **kwargs):
        """Modify account-specific settings.

        Returns status message for operation

        Optional parameters:

            * firstname -- First name
                    Type: String

            * lastname -- Last name
                    Type: String

            * company -- Company
                    Type: String

            * email -- Email (Please note that your email is used for
                authentication purposes such as using this API or logging into
                the Pingdom Panel)
                    Type: String

            * cellphone -- Cellphone (without country code)
                (Requires cellcountrycode and cellcountryiso)
                    Type: String

            * cellcountrycode -- Cellphone country code, for example 1 (USA)
                or 46 (Sweden)
                    Type: Integer

            * cellcountryiso -- Cellphone country ISO code, for example
                US(USA) or SE (Sweden)
                    Type: String

            * phone -- Phone (without country code) (Requires phonecountrycode
                and phonecountryiso)
                    Type: String

            * phonecountrycode -- Phone country code, for example 1 (USA)
                or 46 (Sweden)
                    Type: Integer

            * phonecountryiso -- Phone country ISO code, for example US (USA)
                or SE (Sweden)
                    Type: String

            * address -- Address line 1
                    Type: String

            * address2 -- Address line 2
                    Type: String

            * zip -- Zip, postal code or equivalent
                    Type: String

            * location -- City / location
                    Type: String

            * state -- State, province or equivalent
                    Type: String

            * countryiso -- Country ISO code, for example US (USA)
                or SE (Sweden)
                    Type: String

            * vatcode -- For certain EU countries, VAT-code.
                Example: SE123456789
                    Type: String

            * autologout -- Enable auto-logout
                    Type: Boolean

            * regionid -- Region identifier, for localization purposes.
                0 for "Custom"/none. See the API resource "Reference" for more
                information
                    Type: Integer

            * timezoneid -- Time zone identifier. See the API resource
                "Reference" for more information
                    Type: Integer

            * datetimeformatid -- Date/time format identifier. See the API
                resource "Reference" for more information
                    Type: Integer

            * numberformatid -- Number format identifier. See the API resource
                "Reference" for more information
                    Type: Integer

            * pubrcustomdesign -- Use custom design for public reports
                    Type: Boolean

            * pubrtextcolor -- Public reports, custom text color
                (Example: FEFFFE or 99CC00)
                    Type: String

            * pubrbackgroundcolor -- Public reports, background color
                (Example: FEFFFE or 99CC00)
                    Type: String

            * pubrlogourl -- Public reports, URL to custom logotype.
                This parameter is currently disabled for public use.
                (Example: stats.pingdom.com/images/logo.png)
                    Type: String

            * pubrmonths -- Public reports, nuber of months to show
                    Type: String ['none', 'all', '3']

            * pubrshowoverview -- Public reports, enable overview
                    Type: Boolean

            * pubrcustomdomain -- Public reports, custom domain. Must be a DNS
                CNAME with target stats.pingdom.com
                    Type: Boolean
        """

        # Warn user about unhandled parameters
        for key in kwargs:
            if key not in ['firstname', 'lastname', 'company', 'email',
                           'cellphone', 'cellcountrycode', 'cellcountryiso',
                           'phone', 'phonecountrycode', 'phonecountryiso',
                           'address', 'address2', 'zip', 'location', 'state',
                           'countryiso', 'vatcode', 'autologout', 'regionid',
                           'timezoneid', 'datetimeformatid', 'numberformatid',
                           'pubrcustomdesign', 'pubrtextcolor',
                           'pubrbackgroundcolor', 'pubrlogourl', 'pubrmonths',
                           'pubrshowoverview', 'pubrcustomdomain']:
                sys.stderr.write("'%s'" % key + ' is not a valid argument ' +
                                 'of modifySettings()\n')

        return self.request('PUT', 'settings', kwargs).json()['message']

    def getEmailReports(self):
        """Returns a list of PingdomEmailReport instances."""

        reports = [PingdomEmailReport(self, x) for x in
                   self.request('GET',
                                'reports.email').json()['subscriptions']]

        return reports

    def newEmailReport(self, name, **kwargs):
        """Creates a new email report

        Returns status message for operation

        Optional parameters:

            * checkid -- Check identifier. If omitted, this will be an
                overview report
                    Type: Integer

            * frequency -- Report frequency
                    Type: String ['monthly', 'weekly', 'daily']

            * contactids -- Comma separated list of receiving contact
                identifiers
                    Type: String

            * additionalemails -- Comma separated list of additional receiving
                emails
                    Type: String
        """

        # Warn user about unhandled parameters
        for key in kwargs:
            if key not in ['checkid', 'frequency', 'contactids',
                           'additionalemails']:
                sys.stderr.write("'%s'" % key + ' is not a valid argument ' +
                                 'of newEmailReport()\n')

        parameters = {'name': name}
        for key, value in kwargs.iteritems():
            parameters[key] = value

        return self.request('POST', 'reports.email',
                            parameters).json()['message']

    def getPublicReports(self):
        """Returns a list of public (web-based) reports

        Returned structure:
        [
            {
                'checkid'   : <Integer> Check identifier
                'checkname' : <String> Check name
                'reporturl' : <String> URL to report
            },
            ...
        ]
        """

        return self.request('GET', 'reports.public').json()['public']

    def getSharedReports(self):
        """Returns a list of PingdomSharedReport instances"""

        response = self.request('GET',
                                'reports.shared').json()['shared']['banners']

        reports = [PingdomSharedReport(self, x) for x in response]
        return reports

    def newSharedReport(self, checkid, **kwargs):
        """Create a shared report (banner).

        Returns status message for operation

        Optional parameters:

            * auto -- Automatic period (If false, requires: fromyear,
                frommonth, fromday, toyear, tomonth, today)
                    Type: Boolean

            * type -- Banner type
                    Type: String ['uptime', 'response']

            * fromyear -- Period start: year
                    Type: Integer

            * frommonth -- Period start: month
                    Type: Integer

            * fromday -- Period start: day
                    Type: Integer

            * toyear -- Period end: year
                    Type: Integer

            * tomonth -- Period end: month
                    Type: Integer

            * today -- Period end: day
                    Type: Integer
        """

        # Warn user about unhandled parameters
        for key in kwargs:
            if key not in ['auto', 'type', 'fromyear', 'frommonth', 'fromday',
                           'toyear', 'tomonth', 'today', 'sharedtype']:
                sys.stderr.write("'%s'" % key + ' is not a valid argument ' +
                                 'of newSharedReport()\n')

        parameters = {'checkid': checkid, 'sharedtype': 'banner'}
        for key, value in kwargs.iteritems():
            parameters[key] = value

        return self.request('POST', 'reports.shared',
                            parameters).json()['message']
