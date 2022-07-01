#!/usr/bin/python
# ClearSolaceStats : Solace Admin 
#    clear VPN and router stats
#
# Ramesh Natarajan, Solace PSG

from __future__ import absolute_import, division, print_function, unicode_literals
import sys, os
import getpass
import argparse
import logging, inspect
import textwrap
import time
import yaml
import string

# Import libraries
sys.path.append(os.getcwd() + "/lib")
import POSSolLogger as poslog
import POSSolYaml   as posyaml
import POSSolHttp   as poshttp
import POSSolSemp   as possemp

# Globals
me = "ClearSolaceStats"
myver = "v0.1"


# --------------------------------------------------------------
# main
# --------------------------------------------------------------
def main(argv):
    global logger

    # setup arguments
    p = argparse.ArgumentParser(prog=me,
                                description='ClearSolaceStats: Clear Solace stats',
                                formatter_class=argparse.RawDescriptionHelpFormatter)

    # pr = p.add_argument_group('Required')

    # Required args
    pr = p.add_argument_group("Connection Info")
    pr.add_argument('--host', action="store", required=True, help='Solace router name')

    po = p.add_argument_group("Objects")
    po.add_argument('--vpn', action='store', nargs="+", required=True, help='VPN names')
    po.add_argument('--system', action='store_true', help='Apply to system (eg: clear)')

    po = p.add_argument_group("Optional")
    po.add_argument('--user', dest="username", default="admin", help='CLI username (default: admin)')
    po.add_argument('--password', help='CLI user Password (default: <read from stdin>)')
    po.add_argument('--env', action='store', help='DC or env for file prefix (default: hostname)')
    po.add_argument('-v', '--verbose', action="count", help='Verbose mode: -v verbose, -vv debug, -vvv trace')
    #po.add_argument('--force', action="store_true", help='silently clear', default=False)
    po.add_argument('--purge', action="store_true", help='Purge Queues', default=False)
    po.add_argument('--queues', action="store", nargs="+", help='List of Queues')

    # parse and validate args
    r = p.parse_args()
    r.clearstats = 1;

    if r.env:
        env = r.env
    else:
        env = r.host

    #if r.force:
    #    yn = input('Ignore errors and continue with force flag (y/N) ?')
    #    if yn != "y":
    #        sys.exit(0)
#
    # initialize logging
    log = poslog.POSSolLogger(me, r.verbose).GetLogger()
    if log is None:
        raise Exception("Logger not defined")
    log.note("=== %s (%s) Starting", me, myver)
    log.debug("args %s", r)
    log.debug("env : %s", env)

    # set traceback limit based on verbosity
    sys.tracebacklimit = 0
    if r.verbose:
        sys.tracebacklimit = int(r.verbose)

    if r.vpn and r.vpn[0] == 'all':
        log.error("--vpn all not supported. Pl list VPNs individually")
        sys.exit(0)

    # If password not passed, read from stdin
    if (not r.password):
        r.password = getpass.getpass("Enter password for " + r.username + " : ")

    try:

        # create http connection object
        http = poshttp.POSSolHttp(me, r.host, r.username, r.password)

        # create semp object
        semp = possemp.POSSolSemp(me, http)

        # ---------------------------------------------------------
        # purge queus
        #
        if r.purge:
            vpn = r.vpn[0]
            log.note("Purge Queue not implemented yet")
            sys.exit(0)
        #    if not confirm("Following queues in vpn %s will be purged:\n%s" % (vpn, r.queues)):
        #        sys.exit(0)
        #    if r.queues:
        #        if r.queues[0] == 'all':
        #            semp.PurgeQueues(vpn, semp.GetQueueNames(vpn))
        #        else:
        #            semp.PurgeQueues(vpn, r.queues)

        # ---------------------------------------------------------
        # clear stats
        #
        if r.clearstats:
            if not confirm("All stats in vpn %s will be cleared" % (r.vpn)):
                sys.exit(0)
            # force so missing objects (like DTE) don't stop clear
            semp.Force(True)
            if r.system:
                semp.ClearSystemStats()
            semp.ClearVpnStats(r.vpn)

    except SystemExit as e:
        sys.exit(e)
    except Exception as e:
        log.exception(repr(e))
    except:
        log.exception("Unexpected exception: %s", sys.exc_info()[0])


def confirm(s):
    return True
    print ('----------------------------------------------------------------------------------')
    print (s)
    print ('----------------------------------------------------------------------------------')
    yn = input('Do you want to Proceed (y/N) ?')
    #print ("got {%s}".format(yn))
    if yn.lower() != "y":
        return False
    return True


if __name__ == "__main__":
    main(sys.argv[1:])
