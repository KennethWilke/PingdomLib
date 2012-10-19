import sys
from pingdomlib.analysis import PingdomAnalysis


checktypes = ['http', 'httpcustom', 'tcp', 'ping', 'dns', 'udp', 'smtp',
              'pop3', 'imap']


class PingdomCheck(object):
    """Class representing a check in pingdom

    Attributes:

        * id -- Check identifier
        * name -- Check name
        * type -- Check type
        * lasterrortime -- Timestamp of last error (if any). Format is UNIX
                            timestamp
        * lasttesttime -- Timestamp of last test (if any). Format is UNIX
                           timestamp
        * lastresponsetime -- Response time (in milliseconds) of last test
        * status -- Current status of check
        * resolution -- How often should the check be tested. In minutes
        * hostname -- Target host
        * created -- Creation time. Format is UNIX timestamp
        * contactids -- Identifiers s of contact who should receive alerts
        * sendtoemail -- Send alerts as email
        * sendtosms -- Send alerts as SMS
        * sendtotwitter -- Send alerts through Twitter
        * sendtoiphone -- Send alerts to iPhone
        * sendtoandroid -- Send alerts to Android
        * sendnotificationwhendown -- Send notification when down this many
                                       times
        * notifyagainevery -- Notify again every n result
        * notifywhenbackup -- Notify when back up again"""

    def __init__(self, instantiator, checkinfo=dict()):
        self.pingdom = instantiator
        self.__addDetails__(checkinfo)

    def __getattr__(self, attr):
        # Pull variables from pingdom if unset
        if attr in ['name', 'resolution', 'sendtoemail', 'sendtosms',
                    'sendtotwitter', 'sendtoiphone', 'paused',
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
            if self.pingdom.pushChanges:
                self.modify(**{key: value})
            else:
                object.__setattr__(self, key, value)
        object.__setattr__(self, key, value)

    def __str__(self):
        return "<PingdomCheck (%s)%s is '%s'>" % (self.id, self.name,
                                                  self.status)

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

        Returned structure:
        [
            {
                'id' : <Integer> Analysis id
                'timefirsttest'   : <Integer> Time of test that initiated the
                                             confirmation test
                'timeconfrimtest' : <Integer> Time of the confirmation test
                                               that perfromed the error
                                               analysis
            },
            ...
        ]
        """

        # Warn user about unhandled parameters
        for key in parameters:
            if key not in ['limit', 'offset', 'from', 'to']:
                sys.stderr.write('%s not a valid argument for analysis()\n'
                                 % key)

        response = self.pingdom.request('GET', 'analysis/%s' % self.id,
                                        parameters)

        return [PingdomAnalysis(self, x) for x in response.json['analysis']]

    def __addDetails__(self, checkinfo):
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

        if 'status' in checkinfo and checkinfo['status'] == 'paused':
            object.__setattr__(self, 'paused', True)
        else:
            object.__setattr__(self, 'paused', False)

    def getDetails(self):
        """Update check details, returns dictionary of details"""

        response = self.pingdom.request('GET', 'checks/%s' % self.id)
        self.__addDetails__(response.json['check'])
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
        """Deletes the check from pingdom, CANNOT BE REVERSED!

        Returns status message of operation"""

        response = self.pingdom.request("DELETE", "checks/%s" % self.id)
        return response.json['message']

    def averages(self, **kwargs):
        """Get the average time / uptime value for a specified check and time
            period.

        Optional parameters:

            * from -- Start time of period. Format is UNIX timestamp
                    Type: Integer
                    Default: 0

            * to -- End time of period. Format is UNIX timestamp
                    Type: Integer
                    Default: Current time

            * probes -- Filter to only use results from a list of probes.
                Format is a comma separated list of probe identifiers
                    Type: String
                    Default: All probes

            * includeuptime -- Include uptime information
                    Type: Boolean
                    Default: False

            * bycountry -- Split response times into country groups
                    Type: Boolean
                    Default: False

            * byprobe -- Split response times into probe groups
                    Type: Boolean
                    Default: False

        Returned structure:
        {
            'responsetime' :
            {
                'to'          : <Integer> Start time of period
                'from'        : <Integer> End time of period
                'avgresponse' : <Integer> Total average response time in
                                 milliseconds
            },
            < More can be included with optional parameters >
        }
        """

        # Warn user about unhandled parameters
        for key in kwargs:
            if key not in ['from', 'to', 'probes', 'includeuptime',
                           'bycountry', 'byprobe']:
                sys.stderr.write("'%s'" % key + ' is not a valid argument of' +
                                 '<PingdomCheck.averages()\n')

        response = self.pingdom.request('GET', 'summary.average/%s' % self.id,
                                        kwargs)

        return response.json['summary']

    def hoursofday(self, **kwargs):
        """Returns the average response time for each hour of the day (0-23)
            for a specific check over a selected time period. I.e. it shows you
            what an average day looks like during that time period.

        Optional parameters:

            * from -- Start time of period. Format is UNIX timestamp
                    Type: Integer
                    Default: One week earlpep8 pingdomlib/*.py
ier than 'to'

            * to -- End time of period. Format is UNIX timestamp
                    Type: Integer
                    Default: Current time

            * probes -- Filter to only use results from a list of probes.
                Format is a comma separated list of probe identifiers
                    Type: String
                    Default: All probes

            * uselocaltime -- If true, use the user's local time zone for
                results (from and to parameters should still be specified in
                UTC). If false, use UTC for results.
                    Type: Boolean
                    Default: False

        Returned structure:
        [
            {
                'hour'       : <Integer> Hour of day (0-23). Please note that
                                if data is missing for an individual hour, it's
                                entry will not be included in the result.
                'avgresponse': <Integer> Average response time(in milliseconds)
                                for this hour of the day
            },
            ...
        ]
        """

        # Warn user about unhanled parameters
        for key in kwargs:
            if key not in ['from', 'to', 'probes', 'uselocaltime']:
                sys.stderr.write("'%s'" % key + ' is not a valid argument of' +
                                 '<PingdomCheck.hoursofday()\n')

        response = self.pingdom.request('GET', 'summary.hoursofday/%s' %
                                        self.id, kwargs)

        return response.json['hoursofday']

    def outages(self, **kwargs):
        """Get a list of status changes for a specified check and time period.
            If order is speficied to descending, the list is ordered by newest
            first. (Default is ordered by oldest first.)

        Optional Parameters:

            * from -- Start time of period. Format is UNIX timestamp
                    Type: Integer
                    Default: One week earlier than 'to'

            * to -- End time of period. Format is UNIX timestamp
                    Type: Integer
                    Default: Current time

            * order -- Sorting order of outages. Ascending or descending
                    Type: String ['asc', 'desc']
                    Default: asc

        Returned structure:
        [
            {
                'status'   : <String> Interval status
                'timefrom' : <Integer> Interval start. Format is UNIX timestamp
                'timeto'   : <Integer> Interval end. Format is UNIX timestamp
            },
            ...
        ]
        """

        # Warn user about unhanled parameters
        for key in kwargs:
            if key not in ['from', 'to', 'order']:
                sys.stderr.write("'%s'" % key + ' is not a valid argument of' +
                                 '<PingdomCheck.outages()\n')

        response = self.pingdom.request('GET', 'summary.outage/%s' % self.id,
                                        kwargs)

        return response.json['summary']['states']

    def performance(self, **kwargs):
        """For a given interval in time, return a list of sub intervals with
            the given resolution. Useful for generating graphs. A sub interval
            may be a week, a day or an hour depending on the choosen resolution

        Optional Parameters:

            * from -- Start time of period. Format is UNIX timestamp
                    Type: Integer
                    Default: 10 intervals earlier than 'to'

            * to -- End time of period. Format is UNIX timestamp
                    Type: Integer
                    Default: Current time

            * resolution -- Inteval size
                    Type: String ['hour', 'day', 'week']
                    Default: hour

            * includeuptime -- Include uptime information
                    Type: Boolean
                    Default: False

            * probes -- Filter to only use results from a list of probes.
                Format is a comma separated list of probe identifiers. Can not
                be used if includeuptime is set to true. Also note that this
                can cause intervals to be omitted, since there may be no
                results from the desired probes in them.
                    Type: String
                    Default: All probes

            * order -- Sorting order of sub intervals. Ascending or descending.
                    Type: String ['asc', 'desc']
                    Default: asc

        Returned structure:
        {
            <RESOLUTION> :
            [
                {
                    'starttime'   : <Integer> Hour interval start. Format UNIX
                                     timestamp
                    'avgresponse' : <Integer> Average response time for this
                                     interval in milliseconds
                    'uptime'      : <Integer> Total uptime for this interval in
                                     seconds
                    'downtime'    : <Integer> Total downtime for this interval
                                     in seconds
                    'unmonitored' : <Integer> Total unmonitored time for this
                                     interval in seconds
                },
                ...
            ]
        }
        """

        # Warn user about unhanled parameters
        for key in kwargs:
            if key not in ['from', 'to', 'resolution', 'includeuptime',
                           'probes', 'order']:
                sys.stderr.write("'%s'" % key + ' is not a valid argument of' +
                                 '<PingdomCheck.performance()\n')

        response = self.pingdom.request('GET', 'summary.performance/%s' %
                                        self.id, kwargs)

        return response.json['summary']

    def probes(self, fromtime, totime=None):
        """Get a list of probes that performed tests for a specified check
            during a specified period."""

        args = {'from': fromtime}
        if totime:
            args['to'] = totime

        response = self.pingdom.request('GET', 'summary.probes/%s' % self.id,
                                        args)

        return response.json['probes']

    def results(self, **kwargs):
        """Return a list of raw test results for a specified check

        Optional Parameters:

            * from -- Start time of period. Format is UNIX timestamp
                    Type: Integer
                    Default: 1 day prior to 'to'

            * to -- End time of period. Format is UNIX timestamp
                    Type: Integer
                    Default: Current time

            * probes -- Filter to only show results from a list of probes.
                Format is a comma separated list of probe identifiers
                    Type: String
                    Default: All probes

            * status -- Filter to only show results with specified statuses.
                Format is a comma separated list of (down, up, unconfirmed,
                unknown)
                    Type: String
                    Default: All statuses

            * limit -- Number of results to show
                    Type: Integer (max 1000)
                    Default: 1000

            * offset -- Number of results to skip
                    Type: Integer (max 43200)
                    Default: 0

            * includeanalysis -- Attach available root cause analysis
                identifiers to corresponding results
                    Type: Boolean
                    Default: False

            * maxresponse -- Maximum response time (ms). If set, specified
                interval must not be larger than 31 days.
                    Type: Integer
                    Default: None

            * minresponse -- Minimum response time (ms). If set, specified
                interval must not be larger than 31 days.
                    Type: Integer
                    Default: None

        Returned structure:
        {
            'results' :
            [
                {
                    'probeid'        : <Integer> Probe identifier
                    'time'           : <Integer> Time when test was performed.
                                        Format is UNIX timestamp
                    'status'         : <String> Result status ['up', 'down',
                                        'unconfirmed_down', 'unknown']
                    'responsetime'   : <Integer> Response time in milliseconds
                                        Will be 0 if no response was received
                    'statusdesc'     : <String> Short status description
                    'statusdesclong' : <String> Long status description
                    'analysisid'     : <Integer> Analysis identifier
                },
                ...
            ],
            'activeprobes' : <Integer List> Probe identifiers in result set
        }
        """

        # Warn user about unhanled parameters
        for key in kwargs:
            if key not in ['from', 'to', 'probes', 'status', 'limit', 'offset',
                           'includeanalysis', 'maxresponse', 'minresponse']:
                sys.stderr.write("'%s'" % key + ' is not a valid argument of' +
                                 '<PingdomCheck.results()\n')

        response = self.pingdom.request('GET', 'results/%s' % self.id, kwargs)

        return response.json

    def publishPublicReport(self):
        """Activate public report for this check.

        Returns status message"""

        response = self.pingdom.request('PUT', 'reports.public/%s' % self.id)
        return respose.json['message']

    def removePublicReport(self):
        """Deactivate public report for this check.

        Returns status message"""

        response = self.pingdom.request('DELETE',
                                        'reports.public/%s' % self.id)
        return respose.json['message']
