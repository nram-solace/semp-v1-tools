#!/usr/bin/python
#
# Ramesh Natarajan, Solace PSG 

import sys, os
import getpass
import argparse
import logging, inspect
import textwrap
import yaml
# Import libraries
sys.path.append(os.getcwd()+"/lib")
import POSSolLogger as poslog
import POSSolYaml   as posyam
import POSSolConfig as poscfg
import POSSolHttp   as poshttp
import POSSolSemp   as possemp

# Globals
me = "CreateSolaceVPN"
myver = "v0.4"

#--------------------------------------------------------------
# main
#--------------------------------------------------------------
def main(argv):
   global logger

   # setup arguments
   p = argparse.ArgumentParser( prog=me,
        description='CreateSolaceVPN : Solace Config Management tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''\
 Refer README.txt for additional info and sample usage.
 '''))

   #pr = p.add_argument_group('Required')
   
   # Required args
   pr = p.add_argument_group("Config files")
   pr.add_argument('--cfgfile', '-f',  action="store", dest='configfile', required=True, help='Config file with Solace router and VPN info')
   pr.add_argument('--sitecfg', '-s', required=True, help='site defaults file') 
   pr.add_argument('--pwdfile', '-p', required=False, help='password file') 
   # Optional args
   po = p.add_argument_group("Actions")
   po.add_argument('--create', action='store_true', help='Create objects')
   po.add_argument('--force', action="store_true", help='Ignore errors *** USE WITH CAUTION ***')

   po = p.add_argument_group("Objects")
   po.add_argument('--vpn', action='store', help='Add/Delete VPN and VPN objects')
   po.add_argument('--clientusers', action='store', nargs='+', help='List of Clients')
   po.add_argument('--clientprofiles',  action='store',  nargs='+', help='List of Client profiles')
   po.add_argument('--aclprofiles', action='store',  nargs='+', help='List of ACL profiles')

   po = p.add_argument_group("Optional")
   po.add_argument('--user', dest="username", default="admin", help='CLI username (default: admin)')
   po.add_argument('--password', help='CLI user Password (default: <read from stdin>)') 
   po.add_argument('--vmr', action="store_true", help='Running on VMR (default: No)')
   po.add_argument('-v','--verbose', action="count", help='Verbose mode: -v verbose, -vv debug, -vvv trace')

   # parse and validate args
   r = p.parse_args()

   if r.force:
      yn = raw_input('Ignore errors and continue with force flag (y/N) ?')
      if yn != "y":
        sys.exit(0)

   # initialize logging
   log = poslog.POSSolLogger(me, r.verbose).GetLogger()
   if log is None:
      raise Exception("Logger not defined")
   log.note("=== %s (%s) Starting", me, myver)
   log.debug ("args %s", r)

   # set traceback limit based on verbosity
   sys.tracebacklimit = 0
   if r.verbose:
      sys.tracebacklimit = int(r.verbose)

   cfg = poscfg.POSSolConfig(me, r.configfile, r.sitecfg, r.pwdfile, r.vmr)
   vpn = cfg.GetVpnName()

      # ---------------------------------------------------------
      # dump config and exit
      #
   if r.dump:
     cfg.Dump(r.verbose);
     sys.exit(0)

   if not r.verify:
      if not (r.vpn or r.clientusers or r.clientprofiles or r.aclprofiles or r.queues or r.queuesubs or r.bridges or r.jndi or r.rdps):
         raise Exception("Missing Argument: Atleast one object argument must be provided")

   # If password not passed, read from stdin
   if (not r.password):
      r.password = getpass.getpass("Enter password for "+ r.username+ " : ")
   
   try:

      # create http connection object
      http = poshttp.POSSolHttp(me, cfg.GetHostInfo(), r.username, r.password)

      # create semp object
      semp = possemp.POSSolSemp(me, http, cfg, r.vmr, r.force)

      # ---------------------------------------------------------
      # create objects
      #
      if r.create :
         if r.vpn:
            if vpn != r.vpn:
                log.note("VPN %s from config is different from arg %s", vpn, r.vpn)
                yn = raw_input('Do you want to proceed (y/N) ?')
                if yn != "y":
                   sys.exit(0)
            semp.CreateMsgVpnAndObjects(r.vpn)

         if r.clientusers:
           if r.clientusers[0] == 'all':
               semp.CreateClientUsersAndObjects(vpn)
           else:
               semp.CreateClientUsers(vpn, r.clientusers)

         if r.clientprofiles:
           if r.clientprofiles[0] == 'all':
               semp.CreateClientProfiles(vpn, cfg.GetClientProfileNames())
           else:
               semp.CreateClientProfiles(vpn, r.clientprofiles)

         if r.aclprofiles:
            if r.aclprofiles[0] == 'all':
               semp.CreateACLProfiles(vpn, cfg.GetACLProfileNames())
            else:
               semp.CreateACLProfiles(vpn,  r.aclprofiles)

   except SystemExit as e:
      sys.exit(e)
   except Exception as e:
      log.exception(repr(e))
   except :
      log.exception("Unexpected exception: %s", sys.exc_info()[0])

if __name__ == "__main__":
   main(sys.argv[1:])
