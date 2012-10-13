import sys
from pingdomlib.analysis import PingdomAnalysis


checktypes = ['http', 'httpcustom', 'tcp', 'ping', 'dns', 'udp', 'smtp',
              'pop3', 'imap']


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

    def __setattr__(self, key, value):
        # Autopush changes to attributes
        if key in ['paused', 'resolution', 'contactids', 'sendtoemail',
                   'sendtosms', 'sendtotwitter', 'sendtoiphone',
                   'sendnotificationwhendown', 'notifyagainevery',
                   'notifywhenbackup', 'created', 'hostname', 'status',
                   'lasterrortime', 'lasttesttime', 'url', 'encryption',
                   'port', 'auth', 'shouldcontain', 'shouldnotcontain',
                   'postdata', 'additionalurls', 'stringtosend',
                   'stringtoexpect', 'expectedip', 'nameserver']:
            self.modify(**{key: value})
        object.__setattr__(self, key, value)

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
        """Fills attributes from a dictionary, uses special handling for the
            'type' key"""

        # Auto-load instance attributes from passed in dictionary
        for key in checkinfo:
            if key == 'type':
                if checkinfo[key] in checktypes:
                    self.type = checkinfo[key]
                else:
                    # Take key from type dict, convert to string for type
                    self.type = checkinfo[key].iterkeys().next()

                    # Take value from type dict, store to member of new attrib
                    object.__setattr__(self, self.type,
                                       checkinfo[key].itervalues().next())
            else:
                # Store other key value pairs as attributes
                object.__setattr__(self, key, checkinfo[key])

    def getDetails(self):
        """Update check details, returns dictionary of details"""

        response = self.pingdom.request('GET', 'checks/%s' % self.id)
        self.addDetails(response.json['check'])
        return response.json['check']

    def modify(self, **kwargs):
        """Modify settings for a check. The provided settings will overwrite
            previous values. Settings not provided will stay the same as before
            the update. To clear an existing value, provide an empty value.
            Please note that you cannot change the type of a check once it has
            been created.

        General parameters:

            * name -- Check name
                    Type: String

            * host - Target host
                    Type: String

            * paused -- Check should be paused
                    Type: Boolean

            * resolution -- Check resolution time (in minutes)
                    Type: Integer [1, 5, 15, 30, 60]

            * contactids -- Comma separated list of contact IDs
                    Type: String

            * sendtoemail -- Send alerts as email
                    Type: Boolean

            * sendtosms -- Send alerts as SMS
                    Type: Boolean

            * sendtotwitter -- Send alerts through Twitter
                    Type: Boolean

            * sendtoiphone -- Send alerts to iPhone
                    Type: Boolean

            * sendtoandroid -- Send alerts to Android
                    Type: Boolean

            * sendnotificationwhendown -- Send notification when check is down
                the given number of times
                    Type: Integer

            * notifyagainevery -- Set how many results to wait for in between
                notices
                    Type: Integer

            * notifywhenbackup -- Notify when back up again
                    Type: Boolean

        HTTP check options:

            * url -- Target path on server
                    Type: String

            * encryption -- Use SSL/TLS
                    Type: Boolean

            * port -- Target server port
                    Type: Integer

            * auth -- Username and password for HTTP authentication
                Example: user:password
                    Type: String

            * shouldcontain -- Target site should contain this string.
                Cannot be combined with 'shouldnotcontain'
                    Type: String

            * shouldnotcontain -- Target site should not contain this string.
                Cannot be combined with 'shouldcontain'
                    Type: String

            * postdata -- Data that should be posted to the web page,
                for example submission data for a sign-up or login form.
                The data needs to be formatted in the same way as a web browser
                would send it to the web server
                    Type: String

            * requestheader<NAME> -- Custom HTTP header, replace <NAME> with
                desired header name. Header in form: Header:Value
                    Type: String

        HTTPCustom check options:

            * url -- Target path on server
                    Type: String

            * encryption -- Use SSL/TLS
                    Type: Boolean

            * port -- Target server port
                    Type: Integer

            * auth -- Username and password for HTTP authentication
                Example: user:password
                    Type: String

            * additionalurls -- Colon-separated list of additonal URLS with
                hostname included
                    Type: String

        TCP check options:

            * port -- Target server port
                    Type: Integer

            * stringtosend -- String to send
                    Type: String

            * stringtoexpect -- String to expect in response
                    Type: String

        DNS check options:

            * expectedip -- Expected IP
                    Type: String

            * nameserver -- Nameserver to check
                    Type: String

        UDP check options:

            * port -- Target server port
                    Type: Integer

            * stringtosend -- String to send
                    Type: String

            * stringtoexpect -- String to expect in response
                    Type: String

        SMTP check options:

            * port -- Target server port
                    Type: Integer

            * auth -- Username and password for target SMTP authentication.
                Example: user:password
                    Type: String

            * stringtoexpect -- String to expect in response
                    Type: String

            * encryption -- Use connection encryption
                    Type: Boolean

        POP3 check options:

            * port -- Target server port
                    Type: Integer

            * stringtoexpect -- String to expect in response
                    Type: String

            * encryption -- Use connection encryption
                    Type: Boolean

        IMAP check options:

            * port -- Target server port
                    Type: Integer

            * stringtoexpect -- String to expect in response
                    Type: String

            * encryption -- Use connection encryption
                    Type: Boolean
        """

        # Warn user about unhandled parameters
        for key in kwargs:
            if key not in ['paused', 'resolution', 'contactids', 'sendtoemail',
                           'sendtosms', 'sendtotwitter', 'sendtoiphone',
                           'sendnotificationwhendown', 'notifyagainevery',
                           'notifywhenbackup', 'created', 'type', 'hostname',
                           'status', 'lasterrortime', 'lasttesttime', 'url',
                           'encryption', 'port', 'auth', 'shouldcontain',
                           'shouldnotcontain', 'postdata', 'additionalurls',
                           'stringtosend', 'stringtoexpect', 'expectedip',
                           'nameserver']:
                sys.stderr.write("'%s'" % key + ' is not a valid argument of' +
                                 '<PingdomCheck>.modify()\n')

        response = self.pingdom.request("PUT", 'checks/%s' % self.id, kwargs)

        return response.json['message']

    def delete(self):
        """Deletes the check from pingdom, CANNOT BE REVERSED!"""

        response = self.pingdom.request("DELETE", "checks/%s" % self.id)
        return response.json['message']
