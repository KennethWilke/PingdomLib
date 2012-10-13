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
        self.details = response.text
        return self.details

    def __getattr__(self, attr):
        if attr == 'details':
            return self.getDetails()
