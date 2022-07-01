#!/usr/bin/python
# GetSolaceStats : Solace Admin 
#    Get VPN and router stats for Performance testing
#    Collects VPN stats and writes some to a CSV (Comma seperated value) file
#    The CSV will be used for further analysis, reporting, etc.
#
# Ramesh Natarajan, Solace PSG
# Jul 24, 2017
#    Initial Version

from __future__ import absolute_import, division, print_function, unicode_literals
import sys, os, inspect
import getpass
import argparse
import time

# Globals
g_log = None
g_tvofile = None
g_semp = None
g_vpnstats = None
g_clientstats = None

# Import libraries
sys.path.append(os.getcwd() + "/lib")
import POSSolLogger as poslog
import POSSolHttp   as poshttp
import POSSolSemp   as possemp
import POSSolStats  as posstat

# Globals
me = "GetSolaceStats"
myver = "v0.1"


#--------------------------------------------------------------------------
# getStatsFromRouter
#    Send SEMP XML to gather stats, parse response XML and poulate
#    Python DS with results
#
def getStatsFromRouter (vpn):
    g_log.enter(" %s::%s  vpn: %s", __name__, inspect.stack()[0][3], vpn)
    global g_vpnstats
    global g_clientstats

    g_semp.GetVpnStats(vpn)
    files = g_semp.ReqRespXmlFiles()
    path = os.path.dirname(files[1])
    g_log.debug("Paths (calc): %s", path)
    g_log.info('Response Dir: %s', path)
    stat = posstat.POSSolStats(me, path, None, True, vpn)
    g_log.info('Getting VPN Stats')
    g_vpnstats = stat.VpnStats(vpn)

    g_log.info('Getting Client Stats')
    g_clientstats = stat.ClientStats(vpn)

#---------------------------------------------------------------------------
# writeStatsToFile
#   Process Python DS with stats (populated by getStatsFromRouter)
#   and append the results to machine readable stats CSV file
#
def writeStatsToFile(vpn):
    g_log.enter(" %s::%s  vpn: %s", __name__, inspect.stack()[0][3], vpn)
    # Append stats to TVO file
    ts = time.strftime("%Y%m%d%H%M%S")
    g_log.info ('Adding stats to file %s' %  g_tvofile)
    with open(g_tvofile, 'a') as fd_tvo:

        print(("timestamp={:s},stats=vpn".format(ts)), end=",", file=fd_tvo)
        for k, v in g_vpnstats.items():
            # v.rstrip("\r\n")
            print(("{:s}={:s}".format(k, v)), end=",", file=fd_tvo)
        print(("vpn=%s" % vpn), end="\n", file=fd_tvo)

        print(("timestamp={:s},stats=client".format(ts)), end=",", file=fd_tvo)
        for k, v in g_clientstats.items():
            # v.rstrip("\r\n")
            print(("{:s}={:s}".format(k, v)), end=",", file=fd_tvo)
        print(("vpn=%s" % vpn), end="\n", file=fd_tvo)


# --------------------------------------------------------------
# main
# --------------------------------------------------------------
def main(argv):
    global logger
    global g_log
    global g_tvofile
    global g_semp

    # setup arguments
    p = argparse.ArgumentParser(prog=me,
                                description='GetSolaceStats: Get Solace stats',
                                formatter_class=argparse.RawDescriptionHelpFormatter)

    # pr = p.add_argument_group('Required')

    # Required args
    pr = p.add_argument_group("Connection Info")
    pr.add_argument('--host', action="store", required=True, help='Solace router name')

    po = p.add_argument_group("Objects")
    po.add_argument('--vpn', action='store', required=True, help='VPN name')
    po.add_argument('--system', action='store_true', help='Apply to system')

    po = p.add_argument_group("Optional")
    po.add_argument('--user', dest="username", default="admin", help='CLI username (default: admin)')
    po.add_argument('--password', help='CLI user Password (default: <read from stdin>)')
    po.add_argument('--env', action='store', help='DC or env for file prefix (default: hostname)')
    po.add_argument('-v', '--verbose', action="count", help='Verbose mode: -v verbose, -vv debug, -vvv trace')
    po.add_argument('--loop', action="store_true",  help='Run stats gathering in a loop for-ever')
    po.add_argument('--delay', action="store",  default="20", help='Delay in seconds between stats gathering in a loop')


    # parse and validate args
    r = p.parse_args()

    if r.env:
        env = r.env
    else:
        env = r.host

    # initialize logging
    g_log = poslog.POSSolLogger(me, r.verbose).GetLogger()
    if g_log is None:
        raise Exception("Logger not defined")
    g_log.note("=== %s (%s) Starting", me, myver)
    g_log.debug("args %s", r)
    g_log.debug("env : %s", env)

    # set traceback limit based on verbosity
    sys.tracebacklimit = 0
    if r.verbose:
        sys.tracebacklimit = int(r.verbose)

    if r.vpn and r.vpn[0] == 'all':
        g_log.error("--vpn all not supported. Pl list VPNs individually")
        sys.exit(0)

    # If password not passed, read from stdin
    if (not r.password):
        r.password = getpass.getpass("Enter password for " + r.username + " : ")

    g_tvofile = "out/solace_stats.tvo"
    if not os.path.exists(g_tvofile):
       with open(g_tvofile, 'w') as fd_tvo:
          print ("#Solace Stats", end="\n", file=fd_tvo)

    try:

        vpn = r.vpn
        # create http connection object
        http = poshttp.POSSolHttp(me, r.host, r.username, r.password)

        # create semp object
        g_semp = possemp.POSSolSemp(me, http)

        getStatsFromRouter (vpn)
        writeStatsToFile (vpn)

        # If loop arg is passed, call stats collection and save forever
        if (r.loop):
            delay = int(r.delay)
            if (delay < 10):
                g_log.exception("Loop delay should be greater than 10 seconds")
                sys.exit()
            g_log.note("Looping forever with %s seconds delay", r.delay)
            while (r.loop):
                g_log.debug("Sleeping for %d sec", delay)
                time.sleep(delay)
                getStatsFromRouter (vpn)
                writeStatsToFile (vpn)

    except SystemExit as e:
        sys.exit(e)
    except Exception as e:
        g_log.exception(repr(e))
    except:
        g_log.exception("Unexpected exception: %s", sys.exc_info()[0])


if __name__ == "__main__":
    main(sys.argv[1:])
