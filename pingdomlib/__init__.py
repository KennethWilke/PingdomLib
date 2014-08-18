"""
===============
PingdomLib v1.7
===============
Written by: Kenneth Wilke <kenneth.wilke@gmail.com>

This is a python library to provide full access to the pingdom API, along with
a few additional features to make using the API easier and pythonic.

Usage examples
==============

Connecting to pingdom
---------------------
import pingdomlib
api = pingdomlib.Pingdom(username, password, apikey)

Show all checks that are not in 'UP' status
-------------------------------------------
# See pingdomlib.pingdom documentation to see available calls and settings
pingdomchecks = api.getChecks()
for check in pingdomchecks:
    # See pingdomlib.check documentation for information on PingdomCheck class
    if check.status != 'up':
        print check

Creating a new check
--------------------
newcheck = api.newCheck("New check name", "www.hostnametocheck.com")

Updating a check
----------------
# Updates to check objects are pushed immediately to pingdom
newcheck.paused = True

Disabling change pushing for checks
-----------------------------------
api.pushChanges = False

Get last 10 pingdom alerts sent
-------------------------------
import datetime
for alert in api.alerts(limit=10):
    time = datetime.datetime.fromtimestamp(alert['time'])
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    print "[%s] %s is %s" % (time, alert['name'], alert['status'])

Get outages for a specific check
--------------------------------
import datetime
check = api.getCheck(227878)
for outage in check.outages():
    # timestamp conversion
    time_start = datetime.datetime.fromtimestamp(outage['timefrom'])
    timestamp_start = time_start.strftime('%Y-%m-%d %H:%M:%S')
    time_end = datetime.datetime.fromtimestamp(outage['timeto'])
    timestamp_end = time_end.strftime('%Y-%m-%d %H:%M:%S')

    print "%s: %s from %s to %s [%dm]" % (check.name, outage['status'],
                                          timestamp_start, timestamp_end,
                                          (outage['timeto'] -
                                          outage['timefrom']) / 60)

Contributors
============
* Wil Clouser
* Ash Berlin
* Wu Jiang
* Gertjan Oude Lohuis
* Benjamin Boudreau
* Britt Gresham
* Allard Hoeve

Special thanks
==============
Anders Ekman, Pingdom, for offering warm and helpful support with the API

TODO list
=========
Planned improvements
--------------------
* Optional Gzip Compression
* Improve check update process with pushChanges disabled
"""
from pingdomlib.pingdom import Pingdom
