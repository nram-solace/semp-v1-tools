#!/usr/bin/python
# ConfigureSolaceRouter
#   This file implements provisioning Global Solace Router Objects
# nram, Ramesh Natarajan, Solace PSG
# Aug 15, 2017

import sys, os
import getpass
import argparse
import logging, inspect
import textwrap
import yaml

# Import libraries
sys.path.append(os.getcwd() + "/lib")
import POSSolLogger as poslog
import POSSolJSONConfig as poscfg
import POSSolHttp   as poshttp
import POSSolSemp   as possemp

# Globals
me = "ConfigureSolaceRouter"
myver = "v0.1"


# --------------------------------------------------------------
# main
# --------------------------------------------------------------
def main(argv):
    global logger

    # setup arguments
    p = argparse.ArgumentParser(prog=me,
                                description='ConfigureSolaceRouter : Solace Router Configuration tool',
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog=textwrap.dedent('''\
 Refer README.txt for additional info and sample usage.
 '''))

    # pr = p.add_argument_group('Required')

    # Required args
    pr = p.add_argument_group("Config files")
    pr.add_argument('--cfgfile', required=True, action="store", dest='configfile',
                    help='Config file with Solace router and VPN info')
    pr.add_argument('--router', required=True, dest="router",  help='Solace Appliance/VMR name or IP')

    # Optional args
    po = p.add_argument_group("Actions")
    po.add_argument('--create', action='store_true', help='Create objects')
    po.add_argument('--delete', action='store_true', help='Delete objects')
    po.add_argument('--force', action="store_true", help='Ignore errors *** USE WITH CAUTION ***')

    po = p.add_argument_group("Objects")
    po.add_argument('--cliusers', action='store_true', help='Add/Delete CLI Users')
    po.add_argument('--ldapprofiles', action='store_true', help='Add/Delete LDAP Profiles')


    po = p.add_argument_group("Optional")
    po.add_argument('--user', dest="username", default="admin", help='CLI username (default: admin)')
    po.add_argument('--password', help='CLI user Password (default: <read from stdin>)')
    po.add_argument('--vmr', action="store_true", help='Running on VMR (default: No)')
    po.add_argument('-v', '--verbose', action="count", help='Verbose mode: -v verbose, -vv debug, -vvv trace')

    # parse and validate args
    r = p.parse_args()

    if not (r.create or r.delete):
        raise Exception ("Missing Action Argument. Either create/delete  must be specified")

    if not (r.cliusers or r.ldapprofiles):
        raise Exception ("Missing Router object argument. Either cliuser/ldapprofile must be speccified")

    if r.force:
        yn = raw_input('Ignore errors and continue with force flag (y/N) ?')
        if yn != "y":
            sys.exit(0)

    # initialize logging
    log = poslog.POSSolLogger(me, r.verbose).GetLogger()
    if log is None:
        raise Exception("Logger not defined")
    log.note("=== %s (%s) Starting", me, myver)
    log.debug("args %s", r)

    # set traceback limit based on verbosity
    sys.tracebacklimit = 0
    if r.verbose:
        sys.tracebacklimit = int(r.verbose)

    cfg = poscfg.POSSolJSONConfig(me, r.configfile, r.vmr)

    # If password not passed, read from stdin
    if (not r.password):
        r.password = getpass.getpass("Enter password for " + r.username + " : ")

    try:
        # create http connection object
        http = poshttp.POSSolHttp(me, r.router, r.username, r.password)

        # create semp object
        semp = possemp.POSSolSemp(me, http, cfg, r.vmr, r.force)

        # ---------------------------------------------------------
        # create objects
        #
        if r.create:
            if r.cliusers:
                semp.CreateCliUsers(cfg.m_cliusers)
            if r.ldapprofiles:
                semp.CreateLdapProfiles(cfg.m_ldapprofiles)

        # ---------------------------------------------------------
        # delete objects
        #
        if r.delete:
            if r.cliusers:
                semp.DeleteCliUsers(cfg.m_cliusers)
            if r.ldapprofiles:
                semp.DeleteLdapProfiles(cfg.m_ldapprofiles)

    except SystemExit as e:
        sys.exit(e)
    except Exception as e:
        log.exception(repr(e))
    except:
        log.exception("Unexpected exception: %s", sys.exc_info()[0])

if __name__ == "__main__":
    main(sys.argv[1:])
