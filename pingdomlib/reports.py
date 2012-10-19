class PingdomEmailReport(object):
    """Class represening a pingdom email report

    Attributes:

        * id -- Subscription identifier
        * name -- Subscription name
        * checkid -- Check identifier for check subscriptions
        * frequency -- Report frequency
        * additionalemails -- List additional receiving email addressse
        * contactids -- List of identifiers for receiving contacts
    """

    def __init__(self, instantiator, reportdetails):
        self.pingdom = instantiator

        for key in reportdetails:
            object.__setattr__(self, key, reportdetails[key])

    def __setattr__(self, key, value):
        # Autopush changes to attributes
        if key in ['id', 'name', 'checkid', 'frequency', 'contactids',
                   'additionalemails']:
            if self.pingdom.pushChanges:
                self.modify(**{key: value})
            else:
                object.__setattr__(self, key, value)
        object.__setattr__(self, key, value)

    def modify(self, **kwargs):
        """Modify this email report

        Parameters:

            * name -- Check name
                    Type: String

            * checkid -- Check identifier. If omitted, this will be an overview
                report
                    Type: Integer

            * frequency -- Report frequency
                    Type: String

            * contactids -- Comma separated list of receiving contact
                identifiers
                    Type: String

            * additionalemails -- Comma separated list of additional recipient
                email addresses
                    Type: String
            """

        # Warn user about unhandled parameters
        for key in kwargs:
            if key not in ['name', 'checkid', 'frequency', 'contactids',
                           'additionalemails']:
                sys.stderr.write("'%s'" % key + ' is not a valid argument of' +
                                 '<PingdomEmailReport>.modify()\n')

        response = self.pingdom.request("PUT", 'reports.email/%s' % self.id,
                                        kwargs)

        return response.json['message']

    def delete(self):
        """Delete this email report"""

        response = self.pingdom.request('DELETE', 'reports.email/%s' % self.id)
        return response.json['message']


class PingdomSharedReport(object):
    """Class represening a pingdom shared report

    Attributes:

        * id -- Banner identifier
        * name -- Banner name
        * checkid -- Check identifier
        * auto -- Automatic period activated
        * type -- Banner type
        * url -- Banner URL
        * fromyear -- Period start: year
        * frommonth -- Period start: month
        * fromday -- Period start: day
        * toyear -- Period end: year
        * tomonth -- Period end: month
        * today -- Period end: day
    """

    def __init__(self, instantiator, reportdetails):
        self.pingdom = instantiator

        for key in reportdetails:
            setattr(self, key, reportdetails[key])

    def delete(self):
        """Delete this email report"""

        response = self.pingdom.request('DELETE',
                                        'reports.shared/%s' % self.id)
        return response.json['message']
