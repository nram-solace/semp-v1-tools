#!/usr/bin/python
# POSSolJSONConfig
#   JSON Config file parsing for POSSol package
#
# Ramesh Natarjan (Solace PSG)
# Aug 15, 2017

import sys, os
import re
import yaml
import logging, inspect
import pprint
import json
import time
# import common function
mypath = os.path.dirname(__file__)
sys.path.append(mypath+"/lib")

class POSSolJSONConfig:
   'Solace JSON Parsing implementation'


        #--------------------------------------------------------------
        # Constructor
        #--------------------------------------------------------------
   def __init__(self, me, cfgfile = None, vmr=False):
       self.m_me = me
       self.m_logger = logging.getLogger(me)
       global log
       log = self.m_logger
       log.enter (" %s::%s  config file: %s", __name__, inspect.stack()[0][3], cfgfile)
       if (cfgfile == None):
           log.debug ("Nothing to do here.")
           return

       # read config files
       try :

           # load app config
            with open(cfgfile, 'r') as f:
                self.m_cfg = json.load(f)
                self.m_cliusers = self.m_cfg["CLI_Users"]
                self.m_ldapprofiles = self.m_cfg["LDAP_Profiles"]  #print (self.m_cfg)
            log.trace ("JSON Config: %s", self.m_cfg)
            log.trace ("CLI User Config: %s", self.m_cliusers)
            log.trace ("LDAP Profiles config: %s", self.m_ldapprofiles)

            f.close()
       except:
            log.exception ("unexpected exception", sys.exc_info()[0])
            raise

   def GetVpnName(self):
       return "ROUTER"
