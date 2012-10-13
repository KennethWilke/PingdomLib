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

