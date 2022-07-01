#!/usr/bin/python
# POSSolXml
#   Common XML functions used by Solace Template python scripts
#
# Ramesh Natarjan (Solace PSG)

from __future__ import absolute_import, division, print_function, unicode_literals
import sys
import os
import base64
import string
import re
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import yaml
import logging
import inspect
if sys.version_info[0] == 3:
   import http.client
else:
   import httplib

# import POSSol libs & Classes
mypath = os.path.dirname(__file__)
sys.path.append(mypath + "/lib")


class POSSolXml:
    'Solace SEMP XML Parsing implementation'

    # --------------------------------------------------------------
    # Constructor
    # --------------------------------------------------------------
    def __init__(self, me, xmlstr, fname=None):
        self.m_me = me
        self.m_logger = logging.getLogger(me)
        self.m_logger.enter("%s::%s -e: xml ", __name__, inspect.stack()[0][3])
        # self.m_logger.trace ("%s::%s -e: xml %s", __name__, inspect.stack()[0][3], xmlstr)
        if xmlstr is None and fname is not None:
            self.m_logger.info('Opening XML file %s', fname)
            with open(fname, 'r') as f:
                xmlstr = f.read()
            f.close()
        self.m_xmlstr = xmlstr
        self.m_xmlroot = ET.fromstring(xmlstr)

        self.m_basepath = ""

    # -------------------------------------------------------------------------------
    # Save
    # -------------------------------------------------------------------------------
    def Save(self, fname, tag=""):
        log = self.m_logger
        log.enter("%s::%s -e: fname %s", __name__, inspect.stack()[0][3], fname)
        log.info("Writing %s data to file: %s", tag, fname)
        try:
            dname = os.path.dirname(fname)
            if not os.path.exists(dname):
                log.debug("creating path %s for file", dname)
                os.makedirs(dname)
            f = open(fname, "w")
            print(self.m_xmlstr, file=f)
            f.close()
        except IOError as ex:
            log.exception(ex)
            raise ex
        except:
            log.exception('Unexpected exception', sys.exc_info()[0])
            raise

    # -------------------------------------------------------------------------------
    # BasePath
    # -------------------------------------------------------------------------------
    def BasePath(self, path):
        self.m_logger.enter("%s::%s -e: path %s", __name__, inspect.stack()[0][3], path)
        self.m_basepath = path

    # -------------------------------------------------------------------------------
    # Find : xpath query on xml string
    #
    def FindAll(self, tag):
        global cfg
        self.m_logger.enter("%s::%s -e: %s", __name__, inspect.stack()[0][3], tag)
        k = self.m_basepath + tag
        self.m_logger.debug("Finding %s", k)
        ret = self.m_xmlroot.findall(k)
        if not ret:
            self.m_logger.info("Tag \"%s\" not found in xml data", k)
            return []
        else:
            rlist = []
            for r in ret:
                rlist.append(r.text)
            return rlist

    # -------------------------------------------------------------------------------
    # Find : xpath query on xml string
    # -------------------------------------------------------------------------------
    def Find(self, tag):
        global cfg
        self.m_logger.enter("%s::%s -e: %s", __name__, inspect.stack()[0][3], tag)
        k = self.m_basepath + tag
        self.m_logger.debug("Finding %s", k)
        n = self.m_xmlroot.find(k)
        if n is None:
            self.m_logger.info("Tag \"%s\" not found in xml data", k)
            return None
        else:
            return n.text

    # -------------------------------------------------------------------------------
    # FindAt : xpath query on xml string
    # -------------------------------------------------------------------------------
    def FindAt(self, tag, attr):
        global cfg
        self.m_logger.enter("%s::%s -e: %s @%s", __name__, inspect.stack()[0][3], tag, attr)
        # k = self.m_basepath + tag + "[@" + attr + "]"
        # poscom.vlog ("Finding", k)
        # n = self.m_xmlroot.find(k)
        k = self.m_basepath + tag
        n = self.m_xmlroot.find(k).attrib[attr]
        if n is None:
            self.m_logger.info("Tag \"%s\" not found in response", k)
            return None
        else:
            return n

    # -------------------------------------------------------------------------------
    # findTags :
    #
    def FindTags(self, tags):
        l = self.m_logger
        l.enter("%s::%s -e: %s", __name__, inspect.stack()[0][3], tags)
        cfg = {}
        for k, v in list(tags.items()):
            l.debug("Finding %s", k)
            val = self.Find(k)
            if val is None:
                l.info("Tag %s not found in response", k)
                val = "NA"
            if v is None:
                v = k.split('/')[-1]
            if v.find('/') > 0:
                (v1, v2) = v.split('/')
                l.debug("Adding %s.%s => %s", v1, v2, val)
                if v1 not in cfg:
                    cfg[v1] = {}
                cfg[v1][v2] = val
            else:
                l.debug("Adding %s => %s", v, val)
                cfg[v] = val
        return cfg

    # -------------------------------------------------------------------------------
    # import response parsing
    #
    def GetMsgVpn(self):
        log = self.m_logger
        log.enter("%s::%s", __name__, inspect.stack()[0][3])
        log.info("Adding VPN")
        self.BasePath('./rpc/show/message-vpn/vpn/')
        # s = rxml.Find('name')
        # print "s = " , s
        tags = {"name": "name",
                "max-connections": "max-connections",
                "max-subscriptions": None,
                "semp-over-message-bus-configuration/semp-over-message-bus-allowed": "semp-over-message-bus",
                "event-configuration/large-message-threshold": "large-msg-threshold",
                "event-configuration/event-thresholds[name='connections']/set-percentage": "event-thresholds/connection-set",
                "event-configuration/event-thresholds[name='connections']/clear-percentage": "event-thresholds/connection-clear"}
        vpninfo = self.FindTags(tags)
        vpninfo['large-msg-threshold'] = "%sK" % (vpninfo['large-msg-threshold'])
        # map True/False to yes/no
        tfmap = {'true': 'yes', 'false': 'no'}
        for t in ['semp-over-message-bus']:
            vpninfo[t] = tfmap[vpninfo[t]]
        return vpninfo

    def GetMsgSpool(self):
        self.BasePath('./rpc/show/message-spool/message-vpn/vpn/')
        tags = {"name": "name",
                "maximum-spool-usage-mb": "spool-size",
                "maximum-transactions": "max-transactions",
                "maximum-transacted-sessions": "max-transacted-sessions",
                "maximum-queues-and-topic-endpoints": "max-endpoints",
                "maximum-ingress-flows": "max-ingress-flows",
                "maximum-egress-flows": "max-egress-flows",
                "event-configuration/event-thresholds[name='spool-usage']/set-percentage": "event-thresholds/spool-usage-set",
                "event-configuration/event-thresholds[name='spool-usage']/clear-percentage": "event-thresholds/spool-usage-clear",
                "event-configuration/event-thresholds[name='egress-flows']/set-percentage": "event-thresholds/egress-flows-set",
                "event-configuration/event-thresholds[name='endpoints']/set-percentage": "event-thresholds/endpoints-set",
                "event-configuration/event-thresholds[name='endpoints']/clear-percentage": "event-thresholds/endpoints-clear",
                "event-configuration/event-thresholds[name='egress-flows']/set-percentage": "event-thresholds/egress-flows-set",
                "event-configuration/event-thresholds[name='egress-flows']/clear-percentage": "event-thresholds/egress-flows-clear",
                "event-configuration/event-thresholds[name='ingress-flows']/set-percentage": "event-thresholds/ingress-flows-set",
                "event-configuration/event-thresholds[name='ingress-flows']/clear-percentage": "event-thresholds/ingress-flows-clear",
                }
        spoolinfo = self.FindTags(tags)
        spoolinfo['spool-size'] = "%sM" % (spoolinfo['spool-size'])
        return spoolinfo

    def GetQueueNames(self):
        self.BasePath('./rpc/show/queue/queues/')
        return self.FindAll('queue/name')

    def GetQueues(self):
        self.BasePath('./rpc/show/queue/queues/')
        qnames = self.FindAll('queue/name')
        qinfolist = []
        for qname in qnames:
            qinfo = {}
            tags = {"queue/[name='%s']/info/owner" % (qname): "owner",
                    "queue/[name='%s']/info/quota" % (qname): "max-spool",
                    "queue/[name='%s']/info/max-message-size" % (qname): "max-msg-size",
                    "queue/[name='%s']/info/max-bind-count" % (qname): None,
                    "queue/[name='%s']/info/max-redelivery" % (qname): None,
                    "queue/[name='%s']/info/max-delivered-unacked-msgs-per-flow" % (qname): 'max-unacked-msgs',
                    "queue/[name='%s']/info/access-type" % (qname): None,
                    "queue/[name='%s']/info/reject-msg-to-sender-on-discard" % (qname): None,
                    "queue/[name='%s']/info/others-permission" % (qname): None,
                    "queue/[name='%s']/info/respect-ttl" % (qname): None,
                    "queue/[name='%s']/info/event/event-thresholds/[name='bind-count']/set-percentage" % (
                    qname): "event-thresholds/bind-count-set",
                    "queue/[name='%s']/info/event/event-thresholds/[name='bind-count']/clear-percentage" % (
                    qname): "event-thresholds/bind-count-clear",
                    "queue/[name='%s']/info/event/event-thresholds/[name='spool-usage']/set-percentage" % (
                    qname): "event-thresholds/spool-usage-set",
                    "queue/[name='%s']/info/event/event-thresholds/[name='spool-usage']/clear-percentage" % (
                    qname): "event-thresholds/spool-usage-clear",
                    }
            qinfo = self.FindTags(tags)
            # map True/False to yes/no
            tfmap = {'true': 'yes', 'false': 'no', 'Yes': 'yes', 'No': 'no'}
            for t in ['reject-msg-to-sender-on-discard', 'respect-ttl']:
                qinfo[t] = tfmap[qinfo[t]].lower()
            # convert 'Modify-Topic (1110)' -> modify-topic
            qinfo['others-permission'] = qinfo['others-permission'].split(' ')[0].lower()
            qinfo['name'] = qname
            # Q max-spool is in MB
            qinfo['max-spool'] = "%sM" % (qinfo['max-spool'])
            qinfolist.append(qinfo)
        return qinfolist

    def GetQueueSubscriptions(self):
        self.BasePath('./rpc/show/queue/queues/')
        qnames = self.FindAll('queue/name')
        qsubslist = []
        for qname in qnames:
            qsubs = {}
            qsubs['topic-subscriptions'] = self.FindAll("queue/[name='%s']/subscriptions/subscription/topic" % (qname))
            qsubs['name'] = qname
            qsubslist.append(qsubs)
        return qsubslist

    def GetClientProfiles(self):
        log = self.m_logger
        log.enter("%s::%s", __name__, inspect.stack()[0][3])
        self.BasePath('./rpc/show/client-profile/profiles/')
        cpnames = self.FindAll('profile/name')
        cpinfolist = []
        log.info("Adding Client Profile")
        for cpname in cpnames:
            # skip default profile
            if cpname == 'default' or cpname == '#client-profile':
                log.info("   Skipping %s", cpname)
                continue
            log.info("   Adding %s", cpname)
            cpinfo = {}
            tags = {"profile/[name='%s']/tcp/maximum-tcp-window-size-in-KB" % (cpname): "tcp-win",
                    "profile/[name='%s']/guaranteed-1-queue-min-burst" % (cpname): "g1-queue-min-burst",
                    "profile/[name='%s']/allow-guaranteed-message-send" % (cpname): None,
                    "profile/[name='%s']/allow-guaranteed-message-receive" % (cpname): None,
                    "profile/[name='%s']/allow-guaranteed-endpoint-create" % (cpname): None,
                    "profile/[name='%s']/allow-transacted-sessions" % (cpname): None,
                    "profile/[name='%s']/allow-bridge-connections" % (cpname): None,
                    "profile/[name='%s']/max-connections-per-client-username" % (cpname): 'max-connections',
                    "profile/[name='%s']/maximum-endpoints-per-client-username" % (cpname): 'max-endpoints',
                    "profile/[name='%s']/maximum-ingress-flows" % (cpname): 'max-ingress-flows',
                    "profile/[name='%s']/maximum-egress-flows" % (cpname): 'max-egress-flows',
                    "profile/[name='%s']/max-subscriptions" % (cpname): None,
                    "profile/[name='%s']/maximum-transactions" % (cpname): 'max-transactions',
                    "profile/[name='%s']/maximum-transacted-sessions" % (cpname): 'max-transacted-sessions',
                    }
            cpinfo = self.FindTags(tags)
            cpinfo['name'] = cpname
            # map True/False to yes/no
            tfmap = {'true': 'yes', 'false': 'no'}
            for t in ['allow-guaranteed-message-send', 'allow-guaranteed-message-receive',
                      'allow-guaranteed-endpoint-create', 'allow-bridge-connections', 'allow-transacted-sessions']:
                cpinfo[t] = tfmap[cpinfo[t]]
            # tcp-win is retured in K
            cpinfo['tcp-win'] = "%sK" % cpinfo['tcp-win']
            cpinfolist.append(cpinfo)
        return cpinfolist

    def GetACLProfiles(self):
        log = self.m_logger
        log.enter("%s::%s", __name__, inspect.stack()[0][3])
        self.BasePath('./rpc/show/acl-profile/acl-profiles/')
        aclnames = self.FindAll('acl-profile/profile-name')
        aclinfolist = []
        log.info("Adding ACL Profiles")
        for aclname in aclnames:
            # skip default profile
            if aclname == 'default' or aclname == '#acl-profile':
                log.info("   Skipping %s", aclname)
                continue
            log.info("   Adding %s", aclname)
            tags = {"acl-profile/[profile-name='%s']/client-connect/allow-default-action" % (
            aclname): 'client-connect-default-action',
                    "acl-profile/[profile-name='%s']/publish-topic/allow-default-action" % (
                    aclname): 'publish-topic-default-action',
                    "acl-profile/[profile-name='%s']/subscribe-topic/allow-default-action" % (
                    aclname): 'subscribe-topic-default-action',
                    }
            aclinfo = self.FindTags(tags)
            # map True/False to allow/disallow
            tfmap = {'true': 'allow', 'false': 'disallow'}
            for t in ['client-connect-default-action', 'publish-topic-default-action',
                      'subscribe-topic-default-action']:
                if len(aclinfo[t]) > 0:
                    aclinfo[t] = tfmap[aclinfo[t]]

            # Get ACL exceptions
            aclinfo['client-connect-exceptions'] = self.FindAll(
                "acl-profile/[profile-name='%s']/client-connect/exceptions/exception" % (aclname))
            aclinfo['publish-topic-exceptions'] = self.FindAll(
                "acl-profile/[profile-name='%s']/publish-topic/exceptions/exception" % (aclname))
            aclinfo['subscribe-topic-exceptions'] = self.FindAll(
                "acl-profile/[profile-name='%s']/subscribe-topic/exceptions/exception" % (aclname))

            aclinfo['name'] = aclname
            aclinfolist.append(aclinfo)
        return aclinfolist

    def GetACLExceptions_(self):
        self.BasePath('./rpc/show/acl-profile/acl-profiles/')
        aclnames = self.FindAll('acl-profile/profile-name')
        explist = []
        for acl in aclnames:
            exps = {}
            exps['name'] = acl
            exps['client-connect-excepitions'] = self.FindAll(
                "acl-profile/[profile-name='%s']/client-connect/exceptions/exception" % (acl))
            exps['publish-topic-excepitions'] = self.FindAll(
                "acl-profile/[profile-name='%s']/publish-topic/exceptions/exception" % (acl))
            exps['subscribe-topic-excepitions'] = self.FindAll(
                "acl-profile/[profile-name='%s']/subscribe-topic/exceptions/exception" % (acl))
            explist.append(exps)
        return explist

    def GetClientUsernames(self):
        log = self.m_logger
        log.enter("%s::%s", __name__, inspect.stack()[0][3])
        self.BasePath('./rpc/show/client-username/client-usernames/')
        usernames = self.FindAll('client-username/client-username')
        log.debug("usernames: %s", usernames)
        return usernames

    def GetClientUserInfo(self):
        log = self.m_logger
        log.enter("%s::%s", __name__, inspect.stack()[0][3])
        self.BasePath('./rpc/show/client-username/client-usernames/')
        usernames = self.FindAll('client-username/client-username')
        userinfolist = []
        log.info("Adding Client usernames")
        for username in usernames:
            # skip default profile
            if username == 'default' or username == '#client-username' or re.search('^#', username):
                log.info("   Skipping %s", username)
                continue
            log.info("   Adding %s", username)
            userinfo = {}
            tags = {"client-username/[client-username='%s']/profile" % (username): "client-profile",
                    "client-username/[client-username='%s']/acl-profile" % (username): "acl-profile",
                    }
            userinfo = self.FindTags(tags)
            userinfo['name'] = username
            # NOTE - can't get password.
            userinfo['password'] = 'ONFILE'
            userinfolist.append(userinfo)
        return userinfolist

    def GetHostname(self):
        log = self.m_logger
        log.enter("%s::%s", __name__, inspect.stack()[0][3])
        self.BasePath('./rpc/show/hostname')
        statslist = []
        stats = {}
        tags = {"/hostname": None}
        stats = self.FindTags(tags)
        log.debug("hostname : %s", stats)
        return stats


        # -----------------------------------------------------------------------------------------
        # show stats parsing
        #

    def MsgSpoolDetails(self):
        log = self.m_logger
        log.enter("%s::%s", __name__, inspect.stack()[0][3])
        self.BasePath('./rpc/show/message-spool/message-spool-info/')
        tags = {"ingress-flow-count": None,
                "ingress-flows-allowed": None,
                "active-flow-count": None,
                "inactive-flow-count": None,
                "flows-allowed": None,
                "active-disk-partition-usage": None,
                "transacted-sessions-used": None,
                "max-transacted-sessions": None,
                "config-status": None,
                }
        stats = self.FindTags(tags)
        log.debug("spool details : %s", stats)
        return stats

    def ClientStats0(self):
        log = self.m_logger
        log.enter("%s::%s", __name__, inspect.stack()[0][3])
        self.BasePath('./rpc/show/stats/client/global/stats/')
        tags = {"total-clients": None,
                }
        stats = self.FindTags(tags)
        log.debug("client details : %s", stats)
        return stats

    def VpnClientUserStats(self, vpn):
        log = self.m_logger
        log.enter("%s::%s vpn: %s", __name__, inspect.stack()[0][3], vpn)
        self.BasePath('./rpc/show/client-username/client-usernames/client-username')
        names = self.FindAll('/client-username')
        statslist = []
        stats = {}
        for name in names:
            if self.Find("/[client-username='%s']/message-vpn" % (name)) != vpn:
                continue
            log.debug('looing for stats for %s', name)
            tags = {"/[client-username='%s']/enabled" % (name): None,
                    "/[client-username='%s']/num-clients" % (name): None,
                    "/[client-username='%s']/max-connections" % (name): None,
                    "/[client-username='%s']/max-endpoints" % (name): None,
                    }
            stats[name] = self.FindTags(tags)
            log.debug("%s all clientusername details : %s", name, stats)
        return stats

    # FIXME : this is just dup of  ParseShowMsgVpn
    def VpnQueueStats(self, vpn):
        log = self.m_logger
        log.enter("%s::%s", __name__, inspect.stack()[0][3])
        self.BasePath('./rpc/show/queue/queues/queue')
        names = self.FindAll('/name')
        # names = self.FindAll("/name/info/[message-vpn='%s']" %(vpn))
        statslist = []
        stats = {}
        for name in names:
            # FIXME: hack to fit all vpn support
            if self.Find("/[name='%s']/info/message-vpn" % (name)) != vpn:
                continue
            log.debug('looing for stats for VPN %s Queue %s', vpn, name)
            tags = {"/[name='%s']/info/[message-vpn='%s']/ingress-config-status" % (name, vpn): None,
                    "/[name='%s']/info/[message-vpn='%s']/egress-config-status" % (name, vpn): None,
                    "/[name='%s']/info/[message-vpn='%s']/num-messages-spooled" % (name, vpn): None,
                    "/[name='%s']/info/[message-vpn='%s']/current-spool-usage-in-mb" % (name, vpn): None,
                    "/[name='%s']/info/[message-vpn='%s']/quota" % (name, vpn): None,
                    "/[name='%s']/info/[message-vpn='%s']/total-delivered-unacked-msgs" % (name, vpn): None,
                    "/[name='%s']/info/[message-vpn='%s']/bind-count" % (name, vpn): None,
                    "/[name='%s']/info/[message-vpn='%s']/max-bind-count" % (name, vpn): None,
                    "/[name='%s']/info/[message-vpn='%s']/max-redelivery" % (name, vpn): None,
                    "/[name='%s']/info/[message-vpn='%s']/max-delivered-unacked-msgs-per-flow" % (
                    name, vpn): 'max-unacked-msgs',
                    "/[name='%s']/info/[message-vpn='%s']/message-vpn" % (name, vpn): None,
                    }
            stats[name] = self.FindTags(tags)
        log.trace("%s queue details : %s", vpn, stats)
        return stats

    def VpnSpoolStats(self, vpn):
        log = self.m_logger
        log.enter("%s::%s vpn: %s", __name__, inspect.stack()[0][3], vpn)
        self.BasePath("./rpc/show/message-spool/message-vpn/vpn/[name='%s']" % (vpn))
        statslist = []
        stats = {}
        log.debug('looing for stats for %s', vpn)
        tags = {"/current-queues-and-topic-endpoints": None,
                "/maximum-queues-and-topic-endpoints": None,
                "/current-spool-usage-mb": None,
                "/maximum-spool-usage-mb": None,
                "/current-transacted-sessions": None,
                "/maximum-transacted-sessions": None,
                "/current-egress-flows": None,
                "/maximum-egress-flows": None,
                "/current-ingress-flows": None,
                "/maximum-ingress-flows": None,
                }
        stats[vpn] = self.FindTags(tags)
        log.debug("%s spool details : %s", vpn, stats)
        return stats

    def VpnStats0(self, vpn):
        log = self.m_logger
        log.enter("%s::%s", __name__, inspect.stack()[0][3])
        self.BasePath("./rpc/show/message-vpn/vpn/[name='%s']" % (vpn))
        statslist = []
        stats = {}
        log.debug('looing for stats for %s', vpn)
        tags = {"/enabled": None,
                "/operational": None,
                "/local-status": None,
                "/connections": None,
                "/max-connections": None,
                "/unique-subscriptions": None,
                "/max-subscriptions": None,
                }
        stats[vpn] = self.FindTags(tags)
        log.debug("%s vpn details : %s", vpn, stats)
        return stats

    # stats for performance test metrics
    def VpnStats(self, vpn):
        log = self.m_logger
        log.enter("%s::%s", __name__, inspect.stack()[0][3])
        self.BasePath("./rpc/show/message-vpn/vpn/[name='%s']/stats" % (vpn))
        statslist = []
        stats = {}
        log.debug('looing for stats for %s', vpn)
        tags = {'/current-ingress-rate-per-second': None,
                '/current-egress-rate-per-second': None,
                '/current-ingress-byte-rate-per-second': None,
                '/current-egress-byte-rate-per-second': None,
                '/ingress-discards/total-ingress-discards': None,
                '/egress-discards/total-egress-discards': None,
#                '/ssl-stats/current-ingress-ssl-rate-per-second': None,
#                '/ssl-stats/current-egress-ssl-rate-per-second': None,
#                '/zip-stats/ingress-compression-ratio': None,
#                '/zip-stats/egress-compression-ratio': None,
                }
        stats[vpn] = self.FindTags(tags)
        log.debug("%s vpn details : %s", vpn, stats)
        return stats[vpn]

    def ClientStats(self, vpn):
        log = self.m_logger
        log.enter("%s::%s", __name__, inspect.stack()[0][3])
        self.BasePath("./rpc/show/stats/client/global/stats")
        statslist = []
        stats = {}
        log.debug('looing for stats for %s', vpn)
        tags = {'/total-clients': None,
                '/total-clients-connected': None,
                '/total-clients-connected-with-ssl': None,
                '/total-clients-connected-service-mqtt': None,
                '/total-client-messages-received': None,
                '/total-client-messages-sent': None,
                '/current-ingress-rate-per-second': None,
                '/current-egress-rate-per-second': None,
                '/ingress-discards/total-ingress-discards': None,
                '/egress-discards/total-egress-discards': None
                }
        stats[vpn] = self.FindTags(tags)
        log.debug("%s vpn details : %s", vpn, stats)
        return stats[vpn]

    def ParseAllVpnDetails(self):
        log = self.m_logger
        log.enter("%s::%s", __name__, inspect.stack()[0][3])
        self.BasePath('./rpc/show/message-vpn/vpn')
        names = self.FindAll('/name')
        statslist = []
        stats = {}
        for name in names:
            log.debug('looing for stats for %s', name)
            tags = {"/[name='%s']/enabled" % (name): None,
                    "/[name='%s']/operational" % (name): None,
                    "/[name='%s']/local-status" % (name): None,
                    "/[name='%s']/connections" % (name): None,
                    "/[name='%s']/max-connections" % (name): None,
                    "/[name='%s']/unique-subscriptions" % (name): None,
                    "/[name='%s']/max-subscriptions" % (name): None,
                    }
            stats[name] = self.FindTags(tags)
            log.debug("%s stats : %s", name, stats)
        return stats

    def ParseAllVpnSpoolDetails(self):
        log = self.m_logger
        log.enter("%s::%s", __name__, inspect.stack()[0][3])
        self.BasePath('./rpc/show/message-spool/message-vpn/vpn')
        names = self.FindAll('/name')
        statslist = []
        stats = {}
        for name in names:
            log.debug('looing for stats for %s', name)
            tags = {"/[name='%s']/current-queues-and-topic-endpoints" % (name): None,
                    "/[name='%s']/maximum-queues-and-topic-endpoints" % (name): None,
                    "/[name='%s']/current-spool-usage-mb" % (name): None,
                    "/[name='%s']/maximum-spool-usage-mb" % (name): None,
                    "/[name='%s']/current-transacted-sessions" % (name): None,
                    "/[name='%s']/maximum-transacted-sessions" % (name): None,
                    "/[name='%s']/current-egress-flows" % (name): None,
                    "/[name='%s']/maximum-egress-flows" % (name): None,
                    "/[name='%s']/current-ingress-flows" % (name): None,
                    "/[name='%s']/maximum-ingress-flows" % (name): None,
                    }
            stats[name] = self.FindTags(tags)
            log.debug("%s stats : %s", name, stats)
        return stats

    def ParseAllVpnStats(self):
        log = self.m_logger
        log.enter("%s::%s", __name__, inspect.stack()[0][3])
        self.BasePath('./rpc/show/message-spool/message-spool-info/')
        tags = {}
        stats = self.FindTags(tags)
        log.debug("stats : %s", stats)
        return stats

    def ParseVpnStats(self):
        log = self.m_logger
        log.enter("%s::%s", __name__, inspect.stack()[0][3])
        self.BasePath('./rpc/show/message-spool/message-spool-info/')
        tags = {}
        stats = self.FindTags(tags)
        log.debug("parse stats : %s", stats)
        return stats

    def ParseMsgSpoolStats(self):
        log = self.m_logger
        log.enter("%s::%s", __name__, inspect.stack()[0][3])
        self.BasePath('./rpc/show/message-spool/message-spool-stats/')
        # nothing for now to scrap here .. all runtime stats
        tags = {}
        stats = self.FindTags(tags)
        log.debug("stats : %s", stats)
        return stats

    def ParseVpnClientDetails(self, vpn):
        log = self.m_logger
        log.enter("%s::%s vpn: %s", __name__, inspect.stack()[0][3], vpn)
        self.BasePath('./rpc/show/client/primary-virtual-router/client')
        names = self.FindAll('/name')
        statslist = []
        stats = {}
        for name in names:
            log.debug('looing for stats for %s', name)
            tags = {"/[name='%s']/total-ingress-flows" % (name): None,
                    "/[name='%s']/total-egress-flows" % (name): None,
                    "/[name='%s']/message-vpn" % (name): None,
                    }
            stats[name] = self.FindTags(tags)
            log.debug("%s all client details : %s", name, stats)
        return stats

    def VpnService(self, vpn):
        log = self.m_logger
        log.enter("%s::%s", __name__, inspect.stack()[0][3])
        self.BasePath("./rpc/show/message-vpn/vpn/[name='%s']/services/service" % (vpn))
        slist = []
        stats = {}
        log.debug('looing for key for %s', vpn)
        tags = {"/enabled": None,
                "/[service-name='SMF'][ssl='false'][compressed='false']/enabled": 'smf-plain-status',
                "/[service-name='SMF'][ssl='false'][compressed='false']/port": 'smf-plain-port',
                "/[service-name='SMF'][ssl='false'][compressed='false']/failed-reason": 'smf-plain-failed-reason',

                "/[service-name='SMF'][ssl='false'][compressed='true']/enabled": 'smf-compressed-status',
                "/[service-name='SMF'][ssl='false'][compressed='true']/port": 'smf-compressed-port',
                "/[service-name='SMF'][ssl='false'][compressed='true']/failed-reason": 'smf-plain-compressed-reason',

                "/[service-name='SMF'][ssl='true']/enabled": 'smf-ssl-status',
                "/[service-name='SMF'][ssl='true']/port": 'smf-ssl-port',
                "/[service-name='SMF'][ssl='true']/failed-reason": 'smf-ssl-failed-reason',

                "/[service-name='MQTT'][ssl='false']/enabled": 'mqtt-plain-status',
                "/[service-name='MQTT'][ssl='false']/port": 'mqtt-plain-port',
                "/[service-name='MQTT'][ssl='false']/failed-reason": 'mqtt-plain-failed-reason',

                "/[service-name='MQTT'][ssl='true']/enabled": 'mqtt-ssl-status',
                "/[service-name='MQTT'][ssl='true']/port": 'mqtt-ssl-port',
                "/[service-name='MQTT'][ssl='true']/failed-reason": 'mqtt-ssl-failed-reason',

                "/[service-name='REST'][ssl='false']/enabled": 'rest-plain-status',
                "/[service-name='REST'][ssl='false']/port": 'rest-plain-port',
                "/[service-name='REST'][ssl='false']/failed-reason": 'rest-plain-failed-reason',

                "/[service-name='REST'][ssl='true']/enabled": 'rest-ssl-status',
                "/[service-name='REST'][ssl='true']/port": 'rest-ssl-port',
                "/[service-name='REST'][ssl='true']/failed-reason": 'rest-ssl-failed-reason',

                }
        stats[vpn] = self.FindTags(tags)
        log.debug("%s vpn service details : %s", vpn, stats)
        return stats
