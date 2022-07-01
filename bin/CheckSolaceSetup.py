#!/usr/local/bin/python3
# CheckSolaceSetup
#   Verify Solace router (VMR/Appliance) Env
#
# Ramesh Natarajan, Solace PSG
from __future__ import absolute_import, division, print_function, unicode_literals
import argparse
import sys
import os
import logging
import inspect
import getpass
import yaml
import time
import re

# Import libraries
sys.path.append(os.getcwd() + "/lib")
import POSSolLogger as poslog
import POSSolSemp   as possemp
import POSSolHttp   as poshttp
import POSSolStats  as posstat
import POSSolXml    as posxml
import POSSolYaml as posyaml

# Globals
me = "CheckSolaceSetup"
myver = "v0.2"


# -----------------------------------------------------------------------------------
# main
#
def main(argv):
    global semp, log

    # setup & parse arguments
    p = argparse.ArgumentParser(prog=me)
    pr = p.add_argument_group("Connection Info")
    pr.add_argument('--host', action="store", required=False, help='Solace router name to get stats (real-time)')
    pr.add_argument('--vpn', action="store", required=True, help='VPN to gather stats.')
    pr.add_argument('--hostlist', action="store", required=False, help='Hostlist YAML file')
    pr.add_argument('--sitedefaults', action="store", required=True, help='Site defaults YAML file')


    po = p.add_argument_group("Optional")
    po.add_argument('--user', dest="username", default="admin", help='CLI username (default: admin)')
    po.add_argument('--password', help='CLI user Password (default: <read from stdin>)')
    po.add_argument('-v', '--verbose', action="count", default=0, help='Verbose mode (-vvv for debug)')
    r = p.parse_args()

    log = poslog.POSSolLogger(me, r.verbose).GetLogger()
    if log is None:
        raise Exception("Logger not defined")
    log.note("=== %s (%s) Starting", me, myver)
    log.debug("args %s", r)

    if (not r.host and not r.hostlist):
        log.error("Either host or hostlist argument should me supplied")
        exit

    sitecfg = posyaml.POSSolYaml(me, r.hostlist, r.sitedefaults)
    if r.verbose:
        sitecfg.Dump()
        print ("host list: ", sitecfg.GetHostList())
        print ("vpn list : ", sitecfg.GetVpnList())
        print ("vpn info : ", sitecfg.GetVpnInfo(r.vpn))
        print ("vpn info key : ", sitecfg.GetVpnInfo(r.vpn, 'smf-plain-status'))

    if (sitecfg.GetDefaultPassword() is None):
        password = getpass.getpass("Enter password for " + sitecfg.GetDefaultUser() + " : ")
    else:
        password = sitecfg.GetDefaultPassword()

    try:
        vpn = r.vpn
        for host in sitecfg.GetHostList():
            # create http connection object
            http = poshttp.POSSolHttp(me, host, sitecfg.GetDefaultUser(), password)

            # create semp object
            semp = possemp.POSSolSemp(me, http)

            semp.GetSystemStats(vpn)
            # files =  semp.ReqRespXmlFiles()
            # paths = [os.path.dirname(files[1])]

            # this gets VPN stats response XML
            semp.GetVpnDetails(vpn)
            files = semp.ReqRespXmlFiles()
            path = os.path.dirname(files[1])
            # paths.append(os.path.dirname(files[1]))
            log.debug("Paths (calc): %s", path)


            log.info('Response Dir: %s', path)
            stat = posstat.POSSolStats(me, path, sitecfg, True, vpn)
            stat.SystemStats()

            # skip non application vpns
            # if re.search('default|config-sync', vpn):
            #     continue
            stat.VpnStats(vpn)
            stat.VpnQueueStats(vpn)
            stat.VpnClientUserStats(vpn)
            stat.cleanup()

    except Exception as e:
        log.exception(repr(e))
    except:
        log.exception("Unexpected exception: %s", sys.exc_info()[0])


# -----------------------------------------------------------------------------------
# Start main
#
if __name__ == "__main__":
    main(sys.argv[1:])
