#!/usr/local/bin/python3
# POSSolYaml
#   YAML tools for Solace Template python scripts
#
# Ramesh Natarjan (Solace PSG)

from __future__ import absolute_import, division, print_function, unicode_literals
import sys
import os
import re
import yaml
import logging
import inspect
import pprint
import json
import time

# import common function
mypath = os.path.dirname(__file__)
sys.path.append(mypath + "/lib")


class POSSolYaml:
    'Solace Yaml implementation'

    # --------------------------------------------------------------
    # Constructor
    # --------------------------------------------------------------
    def __init__(self, me, hostlist=None, sitedefaults=None):
        self.m_me = me
        self.m_logger = logging.getLogger(me)
        global log
        log = self.m_logger
        log.enter(" %s::%s  hostlists %s site-defaults %s", __name__, inspect.stack()[0][3], hostlist, sitedefaults)
        if (hostlist is None and sitedefaults is None):
            log.debug("Nothing to do here.")
            return

        # read config files
        try:
            # load valid-tags reference dict
            if (hostlist is not None):
                log.info("Loading hostlist file %s", hostlist)
                self.m_hostlist = self.Load(hostlist)
            if (sitedefaults is not None):
                log.info("Loading site-defaults file %s", sitedefaults)
                self.m_sitedefaults = self.Load(sitedefaults)

        except yaml.YAMLError as ex:
            log.exception('YAMLException', ex)
        except:
            log.exception("unexpected exception", sys.exc_info()[0])
            raise


            # --------------------------------------------------------------
            # Load
            # --------------------------------------------------------------

    def Load(self, fname):
        log = self.m_logger
        log.enter(" %s::%s  %s", __name__, inspect.stack()[0][3], fname)

        log.info("Reading YAML file %s", fname)
        try:
            with open(fname, 'r') as f:
                l_dict = yaml.load(f)
                log.trace("%s file content:\n%s", fname, l_dict)
                f.close()
                return l_dict
        except IOError as ex:
            log.exception(ex)
            raise ex
        except yaml.YAMLError as ex:
            log.exception(ex)
            raise ex
        except:
            log.exception('Unexpected exception', sys.exc_info()[0])
            raise

    # dump cfg
    #
    def Dump(self, verbose=False):
        log = self.m_logger
        log.enter(" %s::%s  ", __name__, inspect.stack()[0][3])
        print("----------\nHost List:\n")
        print((yaml.dump(self.m_hostlist, default_flow_style=False)))
        print("----------\nSite Defaults:\n")
        print((yaml.dump(self.m_sitedefaults, default_flow_style=False)))

    def GetHostList(self):
        return self.m_hostlist['hostlist'] ;
    def GetDefaultPort(self):
        return self.m_hostlist['default']['port'] ;
    def GetDefaultUser(self):
        return self.m_hostlist['default']['username'] ;
    def GetDefaultPassword(self):
        #print (self.m_hostlist['default']['password'])
        return self.m_hostlist['default']['password'] ;
    def GetVpnList (self):
        # NOTE: Python3 returns dict_keys when list.keys() is called
        # not a list as in Python2. So its requied to call list(r.keys()]
        # to make it into a list. This works in both Python 2 & 3
        # https://blog.labix.org/2008/06/27/watch-out-for-listdictkeys-in-python-3
        return [list(r.keys()) for r in self.m_sitedefaults['vpn']]

    def GetRouterInfo(self, key = None):
        log = self.m_logger
        log.enter("%s::%s   key: %s", __name__, inspect.stack()[0][3], key)
        r =  self.m_sitedefaults['router']
        if not r:
            return "NA"
        if key is None:
            return r
        else:
            if not key in r:
                return "NA"
            return (str(r[key]))

    def GetVpnInfo(self, vpn, key = None):
        log = self.m_logger
        log.enter("%s::%s   vpn: %s key: %s", __name__, inspect.stack()[0][3], vpn, key)
        # print ("GetVpnInfo:", vpn)
        # print ("len", len(self.m_sitedefaults['vpn']))
        # print ("[0]", self.m_sitedefaults['vpn'][0])
        # print ("[1]", self.m_sitedefaults['vpn'][1])
        # print ("type[1]", type(self.m_sitedefaults['vpn'][1]))
        # print ("keys[1]", list(self.m_sitedefaults['vpn'][1].keys()))
        # Same deal with filters. In Python 2 it returns a list where as in
        # Python 3, it returns a filter_object. Call list() to return list.
        # this works in both Python 2 and Python 3
        # https://stackoverflow.com/questions/12319025/filters-in-python3
        r = list(filter(lambda d: vpn in list(d.keys()), self.m_sitedefaults['vpn']))
        if not r:
            return "NA"
        if key is None:
            return r[0]
        else:
            if not vpn in r[0]:
                return "NA"
            rv = r[0][vpn]
            if not key in rv:
                return "NA"
            return (str(rv[key]))

    def GetQueueInfo(self, vpn, qname, key=None):
        log = self.m_logger
        log.enter("%s::%s   vpn: %s qname: %s key: %s", __name__, inspect.stack()[0][3],
                  vpn, qname, key)

        vpnqname = "%s-%s" % (vpn, qname)
        r = list(filter(lambda d: vpnqname in list(d.keys()), self.m_sitedefaults['queue']))
        if not r:
            return "NA"
        if key is None:
            return r[0]
        else:
            if not vpnqname in r[0]:
                return "NA"
            rv = r[0][vpnqname]
            if not key in rv:
                return "NA"
            return (str(rv[key]))

    def GetClientUserInfo(self, vpn, uname, key=None):
        log = self.m_logger
        log.enter("%s::%s   vpn: %s uname: %s key: %s", __name__, inspect.stack()[0][3],
                  vpn, uname, key)

        vpnuname = "%s-%s" % (vpn, uname)
        r = list(filter(lambda d: vpnuname in list(d.keys()), self.m_sitedefaults['clientuser']))
        if not r:
            return "NA"
        if key is None:
            return r[0]
        else:
            if not vpnuname in r[0]:
                return "NA"
            rv = r[0][vpnuname]
            if not key in rv:
                return "NA"
            return (str(rv[key]))


def sizeInBytes(su):
    global log
    log.enter(" %s::%s SIZE %s", __name__, inspect.stack()[0][3], su)
    um = {'B': 1, 'K': 1024, 'M': 1048576, 'G': 1073741824}
    if len(su) == 1:
        return int(su)
    p = re.compile('(\d+)\s*(\w+)')
    (s, u) = p.match(str(su)).groups()
    u = u.upper()
    if u and u in list(um.keys()):
        b = int(s) * um[u]
        log.debug("%s (%s %s) -> %d bytes", su, s, u, b)
        return b
    return int(su)


def sizeInKB(s):
    return sizeInBytes(s) / 1024


def sizeInMB(s):
    return sizeInBytes(s) / 1048576


def sizeInGB(s):
    return sizeInBytes(s) / 1073741824
