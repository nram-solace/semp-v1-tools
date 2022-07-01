#!/usr/bin/python
# POSSolSemp
#   Common SEMP related functions used by Solace Template python scripts
#
# Ramesh Natarjan (Solace PSG)

from __future__ import absolute_import, division, print_function, unicode_literals
import sys
import os
import time
import re
import logging
import inspect
from time import gmtime, strftime
from shutil import copyfile


# import POSSol libs & Classes
# mypath = os.path.dirname(__file__)
# sys.path.append(mypath+"/lib")
sys.path.append(os.getcwd() + "/lib")
import POSSolXml as posxml



class POSSolSemp:
    'Solace SEMP XML implementation'

    # --------------------------------------------------------------
    # Constructor
    #  This stores the passed values to class variables
    #
    # Arguments:
    #   prog: program name (used for looking up log handler)
    #   http: http handler to appliance
    #   cfg: vpn config file object. If calling from possoladm (no config)
    #        pass None
    #   vmr: pass True if running on VMR
    #   force: pass True to ignore errors
    #   semp_version: override default semp version
    #
    def __init__(self, prog, http, cfg=None, vmr=False, force=False, semp_version='8_2VMR'):
        self.m_prog = prog
        self.m_logger = logging.getLogger(prog)
        self.m_logger.enter("%s::%s  force %s semp_version %s", __name__, inspect.stack()[0][3], force, semp_version)

        self.m_http = http
        self.m_cfg = cfg
        self.m_vmr = vmr
        self.m_force = force
        self.m_version = semp_version
        self.m_tstamp = time.strftime("%Y%m%d-%H%M%S")
        self.m_reqxmlfile = None
        self.m_respxmlfile = None
        self.m_vpnnames = None

        # --------------------------------------------------------------
        # Force:
        #   set force flag outside of constructor
        #

    def Force(self, f):
        self.m_logger.info("set force %s", f)
        self.m_force = f if True else False

        # --------------------------------------------------------------
        # PassOrRaise
        #   Raise an exception unless force is used
        #

    def PassOrRaise(self, s):
        log = self.m_logger
        if (self.m_force):
            log.note("*** " + s + "(ignored with force)")
            pass
        else:
            log.error(s)
            # log.debug("raising exception %s", s)
            raise Exception(s)

    # -------------------------------------------------------
    # Post a Semp req
    #
    def PostSemp(self, req):
        log = self.m_logger
        log.enter(" %s::%s ", __name__, inspect.stack()[0][3])

        rc = self.m_http.Post(req)
        # log.trace ("HTTP Response = %s", rc)
        if rc is None:
            raise Exception("Null response")
        # response is stored in http object
        return rc

    # -------------------------------------------------------
    # Process a Semp req
    #
    def ProcessSemp(self, tag, req, vpn):
        # self.m_logger.enter (" %s::%s  tag: %s req: %s ", __name__, inspect.stack()[0][3], tag, req)
        log = self.m_logger
        log.enter("%s::%s  tag: %s", __name__, inspect.stack()[0][3], tag)

        # save request and response files
        if self.m_tstamp is None:
            self.m_tstamp = time.strftime("%Y%m%d-%H%M%S")
        if self.m_cfg:
            vpn = self.m_cfg.GetVpnName()
        fname = re.sub('[^0-9a-zA-Z]+', '_', tag)
        # self.m_reqxmlfile = "semp/request/%s-%s/%s.xml" % (vpn, self.m_tstamp, fname)
        self.m_reqxmlfile = "SEMP/request/%s-%s.xml" % (vpn, fname)
        reqxml = posxml.POSSolXml(self.m_prog, req)
        reqxml.Save(self.m_reqxmlfile, "request semp")
        log.trace('Request File: %s Contents:\n%s', fname, req)

        #  post request
        resp = self.PostSemp(req)
        rxml = posxml.POSSolXml(self.m_prog, resp)

        # save response
        # self.m_respxmlfile = "semp/response/%s-%s/%s.xml" % (vpn, self.m_tstamp, fname)
        self.m_respxmlfile = "SEMP/response/%s-%s.xml" % (vpn, fname)
        rxml.Save(self.m_respxmlfile, "response semp")
        log.trace('Response File: %s Contents:\n%s', fname, resp)

        # Copy (tea) to file with timestamp for eventual timeseries analysis
        ts = time.strftime("%Y%m%d%H%M%S")
        respxmltsfile = "SEMP/response/%s-%s_%s.xml" % (vpn, fname, ts)
        log.info("Saving a copy to: %s", respxmltsfile)
        copyfile(self.m_respxmlfile, respxmltsfile)


        # look for known errors in response
        s = rxml.Find('./parse-error')
        if s:
            es = "SEMP Request \"%s\" failed (Reason : %s)" % (tag, s)
            self.PassOrRaise(es)
            # raise Exception(es)
        rc = rxml.FindAt('./execute-result', 'code')
        if rc != "ok":
            rs = rxml.FindAt('./execute-result', 'reason')
            es = "SEMP Request \"%s\" failed (Reason : %s)" % (tag, rs)
            self.PassOrRaise(es)
            return None
            # raise Exception(es)
            # raise posexp.SempFailed(tag, rs, xmlfname)
        self.m_logger.status("%s (status: %s)", tag, rc)
        return resp

    # -------------------------------------------------------
    # ReadSempRequest
    #
    def ReadSempReq(self, fname):
        log = self.m_logger
        log.enter(" %s::%s  fname = %s", __name__, inspect.stack()[0][3], fname)
        sempfile = "SEMP/%s/%s" % (self.m_version, fname)
        self.m_logger.info("Reading semp request template file: %s", sempfile)
        try:
            f = open(sempfile, 'r')
            if not f:
                raise Exception('Unable to open file', sempfile)
            req = f.read()
            self.m_logger.trace("semp req template = %s", req)
            f.close()
            return req
        except IOError as e:
            log.exception(e)
            raise e
        except:
            log.exception('Unexpected exception', sys.exc_info()[0])
            raise

    # -------------------------------------------------------
    # Show version
    #
    def ShowVersionSemp(self):
        self.m_logger.enter(" %s::%s ", __name__, inspect.stack()[0][3])

        r = '<show> <version/> </show>'
        return self.PostSemp(r)

    # --------------------------------------------------------------------
    # Show VPN
    #
    def ShowMsgVpn(self, vpn):
        log = self.m_logger
        log.enter(" %s::%s  vpn = %s", __name__, inspect.stack()[0][3], vpn)
        log.info("   Getting Message VPN %s", vpn)
        req = self.ReadSempReq('MsgVpn/ShowMsgVpn.xml') % (self.m_version, vpn)
        return self.ProcessSemp("ShowMsgVpn", req)

    def ShowMsgSpool(self, vpn):
        log = self.m_logger
        log.enter(" %s::%s  vpn = %s", __name__, inspect.stack()[0][3], vpn)
        log.info("   Getting Message Spool for VPN %s", vpn)
        req = self.ReadSempReq('MsgVpn/ShowMsgSpool.xml') % (self.m_version, vpn)
        return self.ProcessSemp("ShowMsgSpool", req)

    # --------------------------------------------------------------------
    # Show Queues
    #
    def ShowQueues(self, vpn):
        log = self.m_logger
        log.enter(" %s::%s  vpn = %s", __name__, inspect.stack()[0][3], vpn)
        log.info("   Getting Queue details VPN %s", vpn)
        req = self.ReadSempReq('Queue/ShowQueues.xml') % (self.m_version, vpn)
        return self.ProcessSemp("ShowQueue", req)

    def ShowQueueSubscriptions(self, vpn):
        log = self.m_logger
        log.enter(" %s::%s  vpn = %s", __name__, inspect.stack()[0][3], vpn)
        log.info("   Getting Queue subscription details VPN %s", vpn)
        req = self.ReadSempReq('Queue/ShowQueueSubscriptions.xml') % (self.m_version, vpn)
        return self.ProcessSemp("ShowQueueSubscriptions", req)

    # --------------------------------------------------------------------
    # Show Client Profile
    #
    def ShowClientProfiles(self, vpn):
        log = self.m_logger
        log.enter(" %s::%s  vpn = %s", __name__, inspect.stack()[0][3], vpn)
        log.info("   Getting Client profiles for VPN %s", vpn)
        req = self.ReadSempReq('ClientProfile/ShowClientProfiles.xml') % (self.m_version, vpn)
        return self.ProcessSemp("ShowClientProfiles", req)

    # --------------------------------------------------------------------
    # Show ACL Profile
    #
    def ShowACLProfiles(self, vpn):
        log = self.m_logger
        log.enter(" %s::%s  vpn = %s", __name__, inspect.stack()[0][3], vpn)
        log.info("   Getting ACL profiles for VPN %s", vpn)
        req = self.ReadSempReq('ACLProfile/ShowACLProfiles.xml') % (self.m_version, vpn)
        return self.ProcessSemp("ShowACLProfiles", req)

    # --------------------------------------------------------------------
    # Show Client username
    #
    def ShowClientUsernames(self, vpn):
        log = self.m_logger
        log.enter(" %s::%s  vpn = %s", __name__, inspect.stack()[0][3], vpn)
        log.info("   Getting Client Usernames for VPN %s", vpn)
        req = self.ReadSempReq('ClientUser/ShowClientUsernames.xml') % (self.m_version, vpn)
        return self.ProcessSemp("ShowClientUsernames", req)

        # -------------------------------------------------------------------------
        # GET FUNCTIONS
        # -------------------------------------------------------------------------

        # -----------------------------------------------------------------------------------
        # Get VPN
        #

    def GetMsgVpn(self, vpn):
        log = self.m_logger
        log.enter(" %s::%s  %s", __name__, inspect.stack()[0][3], vpn)

        # show message vpn
        resp = self.ShowMsgVpn(vpn)
        rxml = posxml.POSSolXml(self.m_prog, resp)
        vpninfo = rxml.GetMsgVpn()
        log.debug("vpninfo: %s", vpninfo)

        # show message-spool
        resp = self.ShowMsgSpool(vpn)
        rxml = posxml.POSSolXml(self.m_prog, resp)
        spoolinfo = rxml.GetMsgSpool()
        log.debug("spoolinfo: %s", spoolinfo)

        vpninfo = [merge(vpninfo, spoolinfo)]
        log.debug("returning vpn+spoolinfo: %s", vpninfo)
        return vpninfo

        # -----------------------------------------------------------------------------------
        # Get Queues
        #

    def GetQueues(self, vpn):
        log = self.m_logger
        log.enter(" %s::%s  %s", __name__, inspect.stack()[0][3], vpn)

        # show queue
        qinfolist = []
        resp = self.ShowQueues(vpn)
        rxml = posxml.POSSolXml(self.m_prog, resp)
        qinfo = rxml.GetQueues()
        log.trace("qinfo: %s", qinfo)

        # show queue subscriptions
        resp = self.ShowQueueSubscriptions(vpn)
        rxml = posxml.POSSolXml(self.m_prog, resp)
        qsubs = rxml.GetQueueSubscriptions()
        for qi in qinfo:
            qname = qi['name']
            log.debug("looking for qname: %s", qname)
            qs = filter(lambda qsubs: qsubs['name'] == qname, qsubs)[0]
            log.debug("qinfo %s", qi)
            log.debug("qsubs %s", qs)
            qinfolist.append(merge(qi, qs))
        log.trace("qinfolist: %s", qinfolist)
        return qinfolist

        # -----------------------------------------------------------------------------------
        # Get client profiles
        #

    def GetClientProfiles(self, vpn):
        log = self.m_logger
        log.enter(" %s::%s  %s", __name__, inspect.stack()[0][3], vpn)

        resp = self.ShowClientProfiles(vpn)
        rxml = posxml.POSSolXml(self.m_prog, resp)
        cpinfolist = rxml.GetClientProfiles()
        log.debug("client-profile info: %s", cpinfolist)
        return cpinfolist

        # -----------------------------------------------------------------------------------
        # Get ACL profiles
        #

    def GetACLProfiles(self, vpn):
        log = self.m_logger
        log.enter(" %s::%s  %s", __name__, inspect.stack()[0][3], vpn)

        resp = self.ShowACLProfiles(vpn)
        rxml = posxml.POSSolXml(self.m_prog, resp)
        aclinfolist = rxml.GetACLProfiles()
        log.debug("acl-profile info: %s", aclinfolist)

        return aclinfolist

        # -----------------------------------------------------------------------------------
        # Get client user names
        #

    def GetClientUsernames(self, vpn):
        log = self.m_logger
        log.enter(" %s::%s  %s", __name__, inspect.stack()[0][3], vpn)

        resp = self.ShowClientUsernames(vpn)
        rxml = posxml.POSSolXml(self.m_prog, resp)
        names = rxml.GetClientUsernames()
        log.debug("client usernames: %s", names)
        return names

        # -----------------------------------------------------------------------------------
        # Get client usernames
        #

    def GetClientUserInfo(self, vpn):
        log = self.m_logger
        log.enter(" %s::%s  %s", __name__, inspect.stack()[0][3], vpn)

        resp = self.ShowClientUsernames(vpn)
        rxml = posxml.POSSolXml(self.m_prog, resp)
        userinfolist = rxml.GetClientUserInfo()
        log.debug("clientuser info: %s", userinfolist)
        return userinfolist

        # -----------------------------------------------------------------------------------
        # Get queue names
        #

    def GetQueueNames(self, vpn):
        log = self.m_logger
        log.enter(" %s::%s  %s", __name__, inspect.stack()[0][3], vpn)

        resp = self.ShowQueues(vpn)
        rxml = posxml.POSSolXml(self.m_prog, resp)
        names = rxml.GetQueueNames()
        log.debug("queue names: %s", names)
        return names

        # -----------------------------------------------------------------------------------
        # Get all VPN objects
        #

    def GetMsgVpnConfig(self, vpn):
        log = self.m_logger
        log.enter(" %s::%s  %s", __name__, inspect.stack()[0][3], vpn)
        log.note("Getting VPN Config for %s", vpn)

        vpncfg = {}
        vpncfg['vpn'] = self.GetMsgVpn(vpn)
        vpncfg['client-profiles'] = self.GetClientProfiles(vpn)
        vpncfg['acl-profiles'] = self.GetACLProfiles(vpn)
        vpncfg['client-users'] = self.GetClientUserInfo(vpn)
        vpncfg['queues'] = self.GetQueues(vpn)

        return vpncfg
        # no need to make NameMap as VPN YAML cfg doesn't assume or accept it

        # --------------------------------------------------------------------------------
        # Show Stats commands
        #

    def ShowMsgSpoolDetails(self):
        log = self.m_logger
        log.enter(" %s::%s ", __name__, inspect.stack()[0][3])
        log.info("   Getting MsgSpool details")

        # --------------------------------------------------------------------------------
        # Show Stats commands
        #

    def GetSystemStats(self, vpn):
        log = self.m_logger
        log.enter(" %s::%s", __name__, inspect.stack()[0][3])

        ts = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        log.note("[%s] Getting System details", ts)

        log.info("   Processing ShowHostname")
        req = self.ReadSempReq('ShowHostname.xml') % (self.m_version)
        resp = self.ProcessSemp("ShowHostname", req, "Router")

        log.info("   Processing ShowMsgSpoolDetails")
        req = self.ReadSempReq('ShowMsgSpoolDetails.xml') % (self.m_version)
        resp = self.ProcessSemp("ShowMsgSpoolDetails", req, "Router")

        log.info("   Processing ShowMsgSpoolStats")
        req = self.ReadSempReq('ShowMsgSpoolStats.xml') % (self.m_version)
        resp = self.ProcessSemp("ShowMsgSpoolStats", req, "Router")

        log.info("   Processing ShowClientStats")
        req = self.ReadSempReq('ShowClientStats.xml') % (self.m_version)
        resp = self.ProcessSemp("ShowClientStats", req, "Router")

        pxml = {}
        return pxml

    # -------------------------------------------------------------------------------
    # GetVpnDetails
    #  this is called from possolmon -> POSSolStats.py
    #  this generates response XML file which is readin by possolmon.py later
    #  the filename itself is returned by ReqRespXmlFiles method below
    # Arguments:
    #  vpn
    # Returns:
    #  None
    def GetVpnDetails (self, vpn):
        log = self.m_logger
        ts = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        log.enter(" %s::%s vpn: %s", __name__, inspect.stack()[0][3], vpn)

        log.note("[%s] Getting VPN details for VPN %s", ts, vpn)

        # process single vpn
        log.info("   Processing ShowVpnDetails")
        req = self.ReadSempReq('ShowVpnDetails.xml') % (self.m_version, vpn)
        resp = self.ProcessSemp("ShowVpnDetails", req, vpn)

        log.info("   Processing ShowVpnStats")
        req = self.ReadSempReq('ShowVpnStats.xml') % (self.m_version, vpn)
        resp = self.ProcessSemp("ShowVpnStats", req, vpn)

        log.info("   Processing ShowVpnService")
        req = self.ReadSempReq('ShowVpnService.xml') % (self.m_version, vpn)
        resp = self.ProcessSemp("ShowVpnService", req, vpn)

        log.info("   Processing ShowSpoolDetails")
        req = self.ReadSempReq('ShowSpoolDetails.xml') % (self.m_version, vpn)
        resp = self.ProcessSemp("ShowSpoolDetails", req, vpn)

        log.info("   Processing ShowQueueDetails")
        req = self.ReadSempReq('ShowQueueDetails.xml') % (self.m_version, vpn)
        resp = self.ProcessSemp("ShowQueueDetails", req, vpn)

        log.info("   Processing ShowClientDetails")
        req = self.ReadSempReq('ShowClientDetails.xml') % (self.m_version, vpn)
        resp = self.ProcessSemp("ShowClientDetails", req, vpn)

        return {}

    def GetVpnStats (self, vpn):
        log = self.m_logger
        ts = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        log.enter(" %s::%s vpn: %s", __name__, inspect.stack()[0][3], vpn)

        log.note("[%s] Getting VPN stats for VPN %s", ts, vpn)

        log.info("   Processing ShowVpnStats")
        req = self.ReadSempReq('ShowVpnStats.xml') % (self.m_version, vpn)
        resp = self.ProcessSemp("ShowVpnStats", req, vpn)

        log.info("   Processing ShowClientStats")
        req = self.ReadSempReq('ShowClientStats.xml') % (self.m_version)
        resp = self.ProcessSemp("ShowClientStats", req, vpn)
        return {}

    def GetVpnNames(self):
        if self.m_vpnnames is None:
            req = self.ReadSempReq('ShowAllSpoolDetails.xml') % (self.m_version)
            resp = self.ProcessSemp("ShowSpoolDetails", req)
            rxml = posxml.POSSolXml(self.m_prog, resp)
            rxml.BasePath('./rpc/message-spool/message-vpn/vpn')
            self.m_vpnnames = rxml.FindAll('/name')
        return self.m_vpnnames


    # -----------------------------------------------------------------------
    # Provisioning functions - Router Objects
    # -----------------------------------------------------------------------
    def CreateCliUsers (self, cliuserscfg):
        log = self.m_logger
        log.enter(" %s::%s", __name__, inspect.stack()[0][3])

        for c in cliuserscfg:
            log.note("Creating CLI User %s", c["username"])
            req = self.ReadSempReq('CreateCliUser.xml') % (self.m_version, c["username"], c["password"], c["global-access-level"])
            self.ProcessSemp("CreateCliUser", req, "ROUTER")

            req = self.ReadSempReq('ConfigureCliUserVpnAccessLevel.xml') % (self.m_version, c["username"], c["vpn-access-level"])
            self.ProcessSemp("ConfigureCliUserVpnAccessLevel", req, "ROUTER")

            if not (c["vpn-access-exception"].lower() ==  "none"):
                log.note ("VPN access exception not implemented")
                log.info("VPN exception list for CLI user %s ignored", c["username"])

                #vpnname, vpn_access_level = c["vpn-access-exception"].split(":")
                #req = self.ReadSempReq('ConfigureCliUserVpnAccessList.xml') % (self.m_version, c["username"], vpnname, vpn_access_level)
                #self.ProcessSemp("ConfigureCliUserVpnAccessList", req, "ROUTER")
            else:
                log.info("No VPN exception list for CLI user %s", c["username"])
        return None

    def DeleteCliUsers(self, cliuserscfg):
        log = self.m_logger
        log.enter(" %s::%s", __name__, inspect.stack()[0][3])

        for c in cliuserscfg:
            log.note("Deleting CLI User %s", c["username"])
            req = self.ReadSempReq('DeleteCliUser.xml') % (self.m_version, c["username"])
            self.ProcessSemp("CreateCliUser", req, "ROUTER")
        return None

    def CreateLdapProfiles (self, ldapcfg):
        log = self.m_logger
        log.enter(" %s::%s", __name__, inspect.stack()[0][3])

        for c in ldapcfg:
            pname = c["profile-name"]
            log.note("Creating LDAP Profile %s", pname)
            req = self.ReadSempReq('CreateLdapProfile.xml') % (self.m_version, pname)
            self.ProcessSemp("CreateLdapProfile", req, "ROUTER")

            log.note("Configuring Admin DN (%s) for LDAP Profile %s", c["admin-dn"], pname)
            req = self.ReadSempReq('ConfigureLdapAdminDN.xml') % (self.m_version, pname, c["admin-dn"], c["admin-password"])
            self.ProcessSemp("ConfigureLdapAdminDN", req, "ROUTER")

            log.note("Configuring Base DN (%s) for LDAP Profile %s", c["base-dn"], pname)
            req = self.ReadSempReq('ConfigureLdapBaseDN.xml') % (self.m_version, pname,  c["base-dn"])
            self.ProcessSemp("ConfigureLdapBaseDN", req, "ROUTER")

            log.note("Configuring Filter (%s) for LDAP Profile %s", c["filter"], pname)
            req = self.ReadSempReq('ConfigureLdapFilter.xml') % (self.m_version, pname, c["filter"])
            self.ProcessSemp("ConfigureLdapFilter", req, "ROUTER")

            log.note("Configuring TLS for LDAP Profile %s",  pname)
            req = self.ReadSempReq('ConfigureLdapSetTLS.xml') % (self.m_version, pname)
            self.ProcessSemp("ConfigureLdapSetTLS", req, "ROUTER")

            #log.note("Configuring Secondary search (%s) for LDAP Profile %s", c["base-dn"], pname)
            #req = self.ReadSempReq('ConfigureLdapSecondarySearch.xml') % (self.m_version, pname, c["base-dn"])
            #self.ProcessSemp("ConfigureLdapSecondarySearch", req, "ROUTER")

            for sa in c["ldap-servers"]:
                s = sa["server"]
                log.note("Configuring server %s (%d) for LDAP Profile %s", s,  sa["index"], pname)
                req = self.ReadSempReq('ConfigureLdapServer.xml') % (self.m_version, pname, s, sa["index"])
                self.ProcessSemp("ConfigureLdapServer", req, "ROUTER")

        return None


    def DeleteLdapProfiles (self, ldapcfg):
        log = self.m_logger
        log.enter(" %s::%s", __name__, inspect.stack()[0][3])

        for c in ldapcfg:
            pname = c["profile-name"]
            log.note("Deleting LDAP Profile %s", pname)
            for i in range(1,3):
                req = self.ReadSempReq('DeleteLdapServer.xml') % (self.m_version, pname, i)
                self.ProcessSemp("DeleteLdapServer", req, "ROUTER")
            req = self.ReadSempReq('DeleteLdapProfile.xml') % (self.m_version, pname)
            self.ProcessSemp("DeleteLdapProfile", req, "ROUTER")
        return None


    # -------------------------------------------------------------------------
    # UTIL FUNCTIONS
    # -------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------
    # makeNameMap
    # convert { 'name' : 'myname', 'tag' : 'value' }, ... tp
    #         { 'myname' : { 'name' : 'myname', 'tag' : 'value' }, ... }
    # create a destination map (mapd) internally and return
    #

    def makeNameMap(self, maps):
        log = self.m_logger
        log.enter(" %s::%s ", __name__, inspect.stack()[0][3])
        mapd = {}
        for k1 in list(maps.keys()):
            mapd[k1] = {}  # destination map
            log.debug("Processing root key: %s", k1)
            log.trace("record len %d %s", len(maps[k1]), maps[k1])
            vmap2 = {}
            for k2 in maps[k1]:
                log.trace("key/elem = %s/%s", k1, k2)
                v2 = {}
                if 'name' not in k2:
                    continue
                kname = k2['name']
                vmap2[kname] = k2
                log.trace(" - v2[%s] = %s", kname, k2)
            log.trace("mapd[%s] = %s", k1, vmap2)
            mapd[k1] = vmap2
            log.trace("mapd[%s] = %s", k1, vmap2)
        return mapd

    def ReqRespXmlFiles(self):
        return (self.m_reqxmlfile, self.m_respxmlfile)

    def ClearVpnStats(self, vpns):

        for vpn in vpns:
            log = self.m_logger
            log.enter(" %s::%s VPN: %s", __name__, inspect.stack()[0][3], vpn)
            log.note("Clearing VPN stats for %s" % (vpn))

            log.note("   Processing ClearMsgVpnStats")
            req = self.ReadSempReq('ClearMsgVpnStats.xml') % (self.m_version, vpn)
            resp = self.ProcessSemp("ClearMsgVpnStats", req, vpn)

            log.note("   Processing ClearMsgVpnSpoolStats")
            req = self.ReadSempReq('ClearMsgVpnSpoolStats.xml') % (self.m_version, vpn)
            resp = self.ProcessSemp("ClearMsgVpnSpoolStats", req, vpn)

            log.note("   Processing ClearQueueStats")
            req = self.ReadSempReq('ClearQueueStats.xml') % (self.m_version, vpn)
            resp = self.ProcessSemp("ClearQueueStats", req, vpn)

            log.note("   Processing ClearClientStats")
            req = self.ReadSempReq('ClearClientStats.xml') % (self.m_version, vpn)
            resp = self.ProcessSemp("ClearClientStats", req, vpn)

            log.note("   Processing ClearClientUserStats")
            req = self.ReadSempReq('ClearClientUserStats.xml') % (self.m_version, vpn)
            resp = self.ProcessSemp("ClearClientUserStats", req, vpn)

            # -----------------------------------------------------------------------------------
            # non member functions
            #


def merge(source, destination):
    for key, value in list(source.items()):
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value
    return destination
