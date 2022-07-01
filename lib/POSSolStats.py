#!/usr/bin/python
# This file implements Solace system stats capture and display
#
# Ramesh Natarajan, Solace PSG 

import sys
import os
import base64
import string
import re
import xml.etree.ElementTree as ET
import logging
import inspect
import yaml
import time
if sys.version_info[0] == 3:
   import http.client
else:
   import httplib

# Import libraries
sys.path.append(os.getcwd() + "/lib")
import POSSolLogger as poslog
import POSSolSemp   as possemp
import POSSolHttp   as poshttp
import POSSolXml    as posxml


class POSSolStats:
    'Solace Stats implementation'

    # --------------------------------------------------------------
    # Constructor
    # --------------------------------------------------------------
    def __init__(self, prog, path, sitecfg, compact, vpnname="default"):
        self.m_prog = prog
        self.m_logger = logging.getLogger(prog)
        self.m_logger.enter("%s::%s : path %s", __name__, inspect.stack()[0][3], path)

        self.m_vpn = vpnname;
        self.m_syspath = path + "/Router-";
        self.m_vpnpath = path + "/" + self.m_vpn + "-";
        self.m_hostname = 'solace'
        self.m_compact = compact
        self.m_sitecfg = sitecfg

    def SystemStats(self):
        log = self.m_logger
        log.enter("%s::%s ", __name__, inspect.stack()[0][3])

        fname = self.m_syspath + "ShowHostname.xml"
        xml = posxml.POSSolXml(self.m_prog, None, fname)
        log.trace('xml: %s', xml)
        hnm = xml.GetHostname()
        log.trace('hostname: %s', hnm)
        self.m_hostname = hnm['hostname']

        # -----------------------------------------------------
        # message spool details
        #
        fname = self.m_syspath + "ShowMsgSpoolDetails.xml"
        xml = posxml.POSSolXml(self.m_prog, None, fname)
        log.trace('xml: %s', xml)
        mss = xml.MsgSpoolDetails()
        log.trace('mss: %s', mss)

        fname = self.m_syspath + "ShowClientStats.xml"
        xml = posxml.POSSolXml(self.m_prog, None, fname)
        log.trace('xml: %s', xml)
        msd = xml.ClientStats('ROUTER')
        log.trace('msd: %s', msd)

        self.m_msd = msd
        self.m_mss = mss
        # system stats prined below in VpnStats so they can be
        # printed to file


        # -----------------------------------------------------
        # message spool stats
        #

    def VpnStats(self, vpn):
        log = self.m_logger
        log.enter("%s::%s  vpn: %s", __name__, inspect.stack()[0][3], vpn)

        self.m_vpn = vpn

        ts = time.strftime("%Y%m%d-%H%M%S")
        # self.m_ofname = 'log/%s_%s_%s.txt' % (self.m_hostname, vpn, ts)
        self.m_ofname = '%s_%s.txt' % (self.m_hostname, vpn)
        log.info('Opening file %s', self.m_ofname)
        self.m_ofh = open(self.m_ofname, 'w')
        #print >> self.m_ofh, 'Status as of {%s}'.format(time.strftime("%m/%d/%Y %H:%M:%S"))
        # -----------------------------------------------------
        # print system stats for reference
        #
        mss = self.m_mss
        msd = self.m_msd
        #if (self.m_compact):
        #   print ('-----------------------------------------------------------------------------')
        self.printHeader('Router Info')
        mss['config-status-failed-reason'] = mss['config-status']
        if mss['config-status'].find('Enabled') >= 0:
            mss['config-status'] = 'Up'
        else:
            mss['config-status'] = 'Down'
        self.printRouterStatus(mss, 'config-status', 'config-status-failed-reason')

        mss['max-active-disk-partition-usage'] = 100
        msd['max-total-clients'] = 9000
        mss['egress-flows'] = int(mss['active-flow-count']) + int(mss['inactive-flow-count'])
        mss['max-egress-flows'] = int(mss['flows-allowed'])
        mss['ingress-flows'] = int(mss['ingress-flow-count'])
        mss['max-ingress-flows'] = int(mss['ingress-flows-allowed'])
        mss['max-transacted-sessions-used'] = int(mss['max-transacted-sessions'])


        self.printRouterUsage (mss, 'active-disk-partition-usage')
        self.printRouterUsage (msd, 'total-clients')
        self.printRouterUsage (mss, 'egress-flows')
        self.printRouterUsage (mss, 'ingress-flows')
        self.printRouterUsage (mss, 'transacted-sessions-used')

        # vpn details
        #
        fname = self.m_vpnpath + "ShowVpnDetails.xml"
        xml = posxml.POSSolXml(self.m_prog, None, fname)
        log.trace('xml: %s', xml)
        vpnds = xml.VpnStats(vpn)
        log.trace('VPN Stats: %s', vpnds)

        fname = self.m_vpnpath + "ShowVpnService.xml"
        xml = posxml.POSSolXml(self.m_prog, None, fname)
        log.trace('xml: %s', xml)
        vpnservicelist = xml.VpnService(vpn)
        log.trace('VPN Service: %s', vpnservicelist)

        # -----------------------------------------------------
        # Spool details
        fname = self.m_vpnpath + "ShowSpoolDetails.xml"
        xml = posxml.POSSolXml(self.m_prog, None, fname)
        log.trace('xml: %s', xml)
        vpnsp = xml.VpnSpoolStats(vpn)
        log.trace('VPN Spool Stats: %s', vpnsp)

        self.printHeader('VPN Info', vpn)
        vpnd = vpnds[vpn]  # vpn detail
        vpns = vpnsp[vpn]  # spool detail
        vpnservice = vpnservicelist[vpn];

        self.m_vpninfo = vpnservicelist[vpn]
        self.m_vpndetail = vpnds[vpn]
        self.m_vpnspooldetail = vpnsp[vpn]

        vpnd['config-status'] = 'Down'
        vpnd['config-status-failed-reason'] = 'Unknown'
        if vpnd['enabled'].find('true') < 0:
            vpnd['config-status-failed-reason'] = 'Not enabled'
        elif vpnd['local-status'].find('Up') < 0:
            vpnd['config-status-failed-reason'] = 'Local status down'
        elif vpnd['operational'].find('true') < 0:
            vpnd['config-status-failed-reason'] = 'Operationally down'
        else:
            vpnd['config-status'] = "Up"
        self.printVpnStatus (vpnd, 'config-status', 'config-status-failed-reason')

        # -----------------------------------------------------
        # Service status
        #

        self.printVpnStatus (vpnservice, 'smf-plain-status', 'smf-plain-failed-reason')
        self.printVpnStatus (vpnservice, 'smf-ssl-status', 'smf-ssl-failed-reason')
        self.printVpnStatus (vpnservice, 'smf-compressed-status', 'smf-compressed-failed-reason')
        self.printVpnStatus (vpnservice, 'mqtt-plain-status', 'mqtt-plain-failed-reason')
        self.printVpnStatus (vpnservice, 'mqtt-ssl-status', 'mqtt-ssl-failed-reason')
        self.printVpnStatus (vpnservice, 'rest-plain-status', 'rest-plain-failed-reason')
        self.printVpnStatus (vpnservice, 'rest-ssl-status', 'rest-ssl-failed-reason')

        self.printVpnInfo (vpnservice, 'smf-plain-port')
        self.printVpnInfo (vpnservice, 'smf-compressed-port')
        self.printVpnInfo (vpnservice, 'smf-ssl-port')
        self.printVpnInfo (vpnservice, 'mqtt-plain-port')
        self.printVpnInfo (vpnservice, 'mqtt-ssl-port')
        self.printVpnInfo (vpnservice, 'rest-plain-port')
        self.printVpnInfo (vpnservice, 'rest-ssl-port')

        self.printVpnDetail (vpnd, 'connections', 'max-connections')
        self.printVpnDetail (vpnd, 'unique-subscriptions', 'max-subscriptions')
        self.printVpnDetail (vpns, 'current-spool-usage-mb', 'maximum-spool-usage-mb')
        self.printVpnDetail (vpns, 'current-transacted-sessions', 'maximum-transacted-sessions')
        self.printVpnDetail (vpns, 'current-ingress-flows', 'maximum-ingress-flows')
        self.printVpnDetail (vpns, 'current-egress-flows', 'maximum-egress-flows')
        self.printVpnDetail (vpns, 'current-queues-and-topic-endpoints', 'maximum-queues-and-topic-endpoints')

    # capture metrics for performance testing
    def VpnStats(self, vpn):
        log = self.m_logger
        log.enter("%s::%s  vpn: %s", __name__, inspect.stack()[0][3], vpn)

        self.m_vpn = vpn
        fname = self.m_vpnpath + "ShowVpnStats.xml"
        xml = posxml.POSSolXml(self.m_prog, None, fname)
        log.trace('xml: %s', xml)
        stats = xml.VpnStats(vpn)
        #stats['timestamp'] = time.strftime("%Y%m%d %H:%M:%S")
        #stats['vpn'] = vpn
        log.trace('stats: %s', stats)
        return stats 

    def ClientStats(self, vpn):
        log = self.m_logger
        log.enter("%s::%s  vpn: %s", __name__, inspect.stack()[0][3], vpn)

        self.m_vpn = vpn
        fname = self.m_vpnpath + "ShowClientStats.xml"
        xml = posxml.POSSolXml(self.m_prog, None, fname)
        log.trace('xml: %s', xml)
        stats = xml.ClientStats(vpn)
        #stats['timestamp'] = time.strftime("%Y%m%d %H:%M:%S")
        #stats['vpn'] = vpn
        log.trace('stats: %s', stats)
        return stats 

    def VpnQueueStats(self, vpn):
        log = self.m_logger
        log.enter("%s::%s  vpn: %s", __name__, inspect.stack()[0][3], vpn)

        fname = self.m_vpnpath + "ShowQueueDetails.xml"
        xml = posxml.POSSolXml(self.m_prog, None, fname)
        log.trace('xml: %s', xml)
        qs = xml.VpnQueueStats(vpn)
        log.trace('Queue details: %s', qs)

        self.printHeader('Queue Info')
        for q in sorted(qs.keys()):
            log.debug("Processing Queue: %s", q)
            if qs[q]['ingress-config-status'].find('Up') < 0:
                qs[q]['config-status'] = 'Down'
                qs[q]['config-status-failed-reason'] =  'ingress down'
            elif qs[q]['egress-config-status'].find('Up') < 0:
                qs[q]['config-status'] = 'Down'
                qs[q]['config-status-failed-reason'] =  'egress down'
            else:
                qs[q]['config-status'] = 'Up'

            self.printQueueStatus(qs, q, 'config-status', 'config-status-failed-reason')
            if re.search('^BRIDGE', q):
                self.printQueueDetail(qs, q, 'bind-count', 'max-bind-count', True)
            else:
                self.printQueueDetail(qs, q, 'bind-count', 'max-bind-count')
            self.printQueueDetail(qs, q, 'current-spool-usage-in-mb', 'quota')
        return


    def VpnClientUserStats(self, vpn):
        log = self.m_logger
        log.enter("%s::%s  vpn: %s", __name__, inspect.stack()[0][3], vpn)

        fname = self.m_vpnpath + "ShowClientDetails.xml"
        xml = posxml.POSSolXml(self.m_prog, None, fname)
        client_user_stats = xml.VpnClientUserStats(vpn)
        # log.trace('ClientUsername details: %s', cs)
        self.printHeader('Client User Info')
        for cu in sorted(client_user_stats.keys()):
            if client_user_stats[cu]['enabled'].find('true') >= 0:
                client_user_stats[cu]['config-status'] = 'Up'
            else:
                client_user_stats[cu]['config-status'] = 'Down'
            self.printClientUserStatus(client_user_stats, cu, 'config-status', None)


    def printHeader(self, hdr, vpn=None):
        self.m_hdr = hdr
        print ('-----------------------------------------------------------------------------')
        print(hdr+"\n")

    def prs(self, t, v, s):
        if self.m_compact:
            # if re.search('^Up', s) or re.search('^OK', v):
            #   return
            print( "{:15s} {:25s} {:13s} {:s}". format(self.m_hdr, t, s, v)) #, 'is', s, '(', v, ')'))
            #print >> self.m_ofh, self.m_hdr, t, 'is', s, '(', v, ')'
            return
        print(('{:40s} {:>29s} {:10s}'.format(t, v, s)))
        #print >> self.m_ofh, '{:40s} {:>29s} {:10s}'.format(t, v, s)


    def printRouterStatus(self, mapinfo, tag, failreasontag):
        log = self.m_logger
        log.enter("%s::%s   tag: %s failed-reason-tag: %s", __name__, inspect.stack()[0][3],
                  tag, failreasontag)

        cfg = self.m_sitecfg
        ptag = tag.replace("-", " ")
        val = "Up"
        if mapinfo[tag].find('Up') < 0:
            val = "Down"
        comments = "OK"
        cfgval = cfg.GetRouterInfo(tag)
        log.debug("router tag %s returned %s", tag, cfgval)
        if cfgval == "NA":
            comments = "OK"
        elif val.lower() != cfgval.lower():
            comments = "ERROR: Expecting %s" % cfgval
        pval = "%s - %s" % (val, mapinfo[failreasontag])
        print("  {:>10s} {:35s} {:30s} {:s}".format('Router', ptag, pval, comments))
        return

    def printRouterDetail (self, mapinfo, tag, maxtag, ignoremaxchk = False):
        log = self.m_logger
        log.enter("%s::%s   tag: %s maxtag: %s ingoremaxcheck: %s", __name__, inspect.stack()[0][3],
                  tag, maxtag, ignoremaxchk)

        vpn = self.m_vpn ;
        cfg = self.m_sitecfg ;
        val = int(float(mapinfo[tag]));
        maxval = int(mapinfo[maxtag]);
        ptag = tag.replace("-", " ")
        cfgval = cfg.GetVpnInfo(vpn, tag)
        minvaltag = "min-%s" % tag
        cfgminval = cfg.GetVpnInfo(vpn, minvaltag)
        minval = 0 if cfgminval == "NA" else int(cfgminval)
        if val < minval:
            comments = 'WARNING: Expecting atleast %s' % minval
        else:
            comments = self.getPercentUsageComment(val, maxval)
        print( "  {:10s} {:35s} {:>5d}/{:<24d} {:s}". format(vpn, ptag, val, maxval, comments))
        return

    def printRouterUsage (self, mapinfo, tag, maxok = True):
        log = self.m_logger
        maxtag = "max-%s" % tag
        log.enter("%s::%s   tag: %s failed-reason-tag: %s", __name__, inspect.stack()[0][3],
                  tag, maxtag)

        cfg = self.m_sitecfg
        ptag = tag.replace("-", " ")
        val =  float(mapinfo[tag])
        maxval = float(mapinfo[maxtag])
        log.debug("val:%f maxval: %f", val, maxval)
        if maxval <= 0:
            percentusage = 0
        else:
            percentusage = 100.0 * val / maxval
        pval = "%4.1f%% (%.0f/%.0f)" % (percentusage, val, maxval)
        cfgval = cfg.GetRouterInfo(tag)
        mincfgval = cfg.GetRouterInfo("min-%s" % tag)
        maxcfgval = cfg.GetRouterInfo("max-%s" % tag)
        log.debug("mincfgval: %s maxcfgval: %s", mincfgval, maxcfgval)
        comments = "OK"

        if (mincfgval != "NA"):
            if val < int(mincfgval):
                comments = "ERROR: Expecting atleast %s" % mincfgval
        if (maxcfgval != "NA"):
            if val > int(maxcfgval):
                comments = "ERROR: Expecting atmost %s" % maxcfgval
        log.debug("router tag %s returned %s", tag, cfgval)
        print("  {:>10s} {:35s} {:30s} {:s}".format('Router', ptag, pval, comments))
        return


    def printVpnStatus (self, mapinfo, tag, failreasontag):
        log = self.m_logger
        log.enter("%s::%s   tag: %s failed-reason-tag: %s", __name__, inspect.stack()[0][3],
                  tag, failreasontag)

        vpn = self.m_vpn
        cfg = self.m_sitecfg
        ptag = tag.replace("-", " ")
        cfgval = cfg.GetVpnInfo(vpn, tag)
        log.debug("site-config VPN %s tag %s => %s",vpn,  tag, cfgval)
        val = "Down"
        if mapinfo[tag].find('true') >= 0 or mapinfo[tag].find('Up') >= 0:
            val = "Up"
        else:
            val = "Down - %s" % mapinfo[failreasontag]
        comments = "OK"
        if cfgval == "NA":
            comments = "WARNING: NA"
        elif val.lower() != cfgval.lower():
            comments = "ERROR: Expecting %s" % cfgval
        print( "  {:10s} {:35s} {:30s} {:s}". format(vpn, ptag, val, comments))
        return

    def printVpnDetail (self, mapinfo, tag, maxtag, ignoremaxchk = False):
        log = self.m_logger
        log.enter("%s::%s   tag: %s maxtag: %s ingoremaxcheck: %s", __name__, inspect.stack()[0][3],
                  tag, maxtag, ignoremaxchk)

        vpn = self.m_vpn ;
        cfg = self.m_sitecfg ;
        val = int(float(mapinfo[tag]));
        maxval = int(mapinfo[maxtag]);
        ptag = tag.replace("-", " ")
        cfgval = cfg.GetVpnInfo(vpn, tag)
        minvaltag = "min-%s" % tag
        cfgminval = cfg.GetVpnInfo(vpn, minvaltag)
        minval = 0 if cfgminval == "NA" else int(cfgminval)
        if val < minval:
            comments = 'WARNING: Expecting atleast %s' % minval
        else:
            comments = self.getPercentUsageComment(val, maxval)
        print( "  {:10s} {:35s} {:>5d}/{:<24d} {:s}". format(vpn, ptag, val, maxval, comments))
        return


    def printVpnInfo (self, mapinfo, tag):
        log = self.m_logger
        log.enter("%s::%s  tag: %s", __name__, inspect.stack()[0][3], tag)
        vpn = self.m_vpn ;
        cfg = self.m_sitecfg ;
        val = mapinfo[tag];
        ptag = tag.replace("-", " ")
        cfgval = cfg.GetVpnInfo(vpn, tag)
        comments = "OK"
        if val.lower() != cfgval.lower():
            comments = "ERROR: Expecting %s" % cfgval
        print( "  {:10s} {:35s} {:30s} {:s}". format(vpn, ptag, val, comments))
        return

    def printQueueStatus (self, mapinfo, qname, tag, failreasontag):
        log = self.m_logger
        log.enter("%s::%s   qname: %s tag: %s failed-reason-tag: %s", __name__, inspect.stack()[0][3],
                  qname, tag, failreasontag)

        vpn = self.m_vpn ;
        cfg = self.m_sitecfg ;
        ptag = tag.replace("-", " ")
        val = "Up"
        if mapinfo[qname][tag] != "Up":
            val = "Down - %s" % mapinfo[qname][failreasontag]
        comments = "OK"
        cfgval = cfg.GetQueueInfo(vpn, qname, tag)
        log.debug("vpn %s queue %s tag %s returned %s", vpn,qname, tag, cfgval)
        if cfgval == "NA":
            comments = "OK"
        elif val.lower() != cfgval.lower():
            comments = "ERROR: Expecting %s" % cfgval
        print( "  {:>20s} {:35s} {:20s} {:s}". format(qname, ptag, val, comments))

        return

    def printQueueDetail (self, mapinfo, qname, tag, maxtag, ignoremaxchk = False):
        log = self.m_logger
        log.enter("%s::%s  qname: %s tag: %s maxtag: %s ingoremaxcheck: %s", __name__, inspect.stack()[0][3],
                  qname, tag, maxtag, ignoremaxchk)
        vpn = self.m_vpn ;
        cfg = self.m_sitecfg ;
        mapinfo = mapinfo[qname]
        val = int(float(mapinfo[tag]));
        maxval = int(mapinfo[maxtag]);
        ptag = tag.replace("-", " ")
        cfgval = cfg.GetVpnInfo(vpn, tag)
        minvaltag = "min-%s" % tag
        cfgminval = cfg.GetQueueInfo(vpn, qname, minvaltag)
        log.debug("%s-%s tag %s received %s", vpn, qname, minvaltag, cfgminval)
        minval = 0 if cfgminval == "NA" else int(cfgminval)
        if val < minval:
            comments = 'WARNING: Expecting atleast %s' % minval
        else:
            comments = self.getPercentUsageComment(val, maxval)
        print( "  {:>20s} {:35s} {:>5d}/{:<14d} {:s}". format(qname, ptag, val, maxval, comments))
        return

    def printClientUserStatus (self, mapinfo, uname, tag, failreasontag):
        log = self.m_logger
        log.enter("%s::%s   client-user-name: %s tag: %s failed-reason-tag: %s", __name__, inspect.stack()[0][3],
                  uname, tag, failreasontag)

        vpn = self.m_vpn ;
        cfg = self.m_sitecfg ;
        ptag = tag.replace("-", " ")
        val = "Up"
        if mapinfo[uname][tag] != "Up":
            val = "Down"
        comments = "OK"
        cfgval = cfg.GetClientUserInfo(vpn, uname, tag)
        log.debug("vpn %s user %s tag %s returned %s", vpn,uname, tag, cfgval)
        if cfgval == "NA":
            comments = "OK"
        elif val.lower() != cfgval.lower():
            comments = "ERROR: Expecting %s" % cfgval
        print( "  {:>20s} {:35s} {:20s} {:s}". format(uname, ptag, val, comments))

        return

    def prs2 (self, tname, tag, status):
        ptag = tag.replace("-", " ")
        comments = "OK"
        print("  {:>20s} {:35s} {:20s} {:s}".format(tname, ptag, status, comments))


    def prt(self, t, v, vmax, vmin=0, maxok=False):
        if vmax == 0:
            s = 'NA'
            vp = 0
        else:
            vp = 100.0 * v / vmax
            if maxok:
                s = 'OK'
            elif vp >= 80:
                s = 'CRITICAL'
            elif vp >= 60:
                s = 'WARNING'
            else:
                s = 'OK'
        if v < vmin:
            s = 'Too low'
        if self.m_compact:
            print( "{:15s} {:25s} {:>4.0f}/{:<6.0f} {:}".format(self.m_hdr, t, v, vmax, s))
            #print((self.m_hdr, t, " is ", s, ": ", v, "/", vmax, "used"))
            # print '{:s} {:s} is {:s} ({:d}/{:d} - {:6.2f}%)' . format(self.m_hdr, t, s, v, vmax, vp)
            # print >> self.m_ofh, '{:s} {:s} is {:s} ({:d}/{:d} - {:6.2f}%)' . format(self.m_hdr, t, s, v, vmax, vp)
            return
        print(('{:40s} {:10d} {:10d} {:6.2f}% {:10s}'.format(t, int(v), vmax, vp, s)))
        #print >> self.m_ofh, '{:40s} {:10d} {:10d} {:6.2f}% {:10s}'.format(t, int(v), vmax, vp, s)

    def cleanup(self):
        log = self.m_logger
        log.enter(" %s::%s ", __name__, inspect.stack()[0][3])
        print ('-----------------------------------------------------------------------------')
        # log.note ("Status file %s", self.m_ofname)
        #self.m_ofh.close()

    def getPercentUsageComment(self, val, maxval, ignoremaxchk = False):
        if maxval == 0:
            return 'NA'
        if ignoremaxchk:
            return 'OK'
        valpercent = 100.0 * val / maxval
        if valpercent >= 80:
            return 'CRITICAL: Aboove 80% use'
        if valpercent >= 60:
            return 'WARNING: Above 60% use'
        return 'OK'
