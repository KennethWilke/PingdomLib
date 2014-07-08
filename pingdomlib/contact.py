import sys


class PingdomContact(object):
    """Class representing a pingdom contact

    Attributes:

        * id -- Contact identifier
        * name -- Contact name
        * email -- Contact email
        * cellphone -- Contact cellphone
        * countryiso -- Cellphone country ISO code
        * defaultsmsprovider -- Default SMS provider
        * twitteruser -- Twitter username
        * directtwitter -- Send tweets as direct messages
        * iphonetokens -- List of iPhone tokens
        * androidtokens -- List of android tokens
        * paused -- True if contact is paused
        """

    def __init__(self, instantiator, contactinfo=dict()):
        self.pingdom = instantiator
        self.__addDetails__(contactinfo)

    def __setattr__(self, key, value):
        # Autopush changes to attributes
        if key in ['name', 'email', 'cellphone', 'countryiso',
                   'defaultsmsprovider', 'directtwitter', 'twitteruser',
                   'iphonetokens', 'androidtokens', 'paused']:
            if self.pingdom.pushChanges:
                self.modify(**{key: value})
            else:
                object.__setattr__(self, key, value)
        object.__setattr__(self, key, value)

    def __addDetails__(self, contactinfo):
        """Fills attributes from a dictionary"""

        # Auto-load instance attributes from passed in dictionary
        for key in contactinfo:
            object.__setattr__(self, key, contactinfo[key])

    def modify(self, **kwargs):
        """Modify a contact.

        Returns status message

        Optional Parameters:

            * name -- Contact name
                    Type: String

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
                           'twitteruser', 'name']:
                sys.stderr.write("'%s'" % key + ' is not a valid argument ' +
                                 'of <PingdomContact>.modify()\n')

        response = self.pingdom.request('PUT', 'contacts/%s' % self.id, kwargs)

        return response.json()['message']

    def delete(self):
        """Deletes a contact. CANNOT BE REVERSED!

        Returns status message"""

        response = self.pingdom.request('DELETE', 'contacts/%s' % self.id)
        return response.json()['message']
