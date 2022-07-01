#!/usr/bin/python
# POSSolHttp
#   Common HTTP functions used by Solace Tempale python scripts
#
# Ramesh Natarjan (Solace PSG) 

from __future__ import absolute_import, division, print_function, unicode_literals
import sys
import os
import base64
import string
import re
import xml.etree.ElementTree as ET
import logging
import inspect
if sys.version_info[0] == 3:
   import http.client as http
else:
   import httplib as http

# import POSSol libs & Classes
# mypath = os.path.dirname(__file__)
# sys.path.append(mypath+"/lib")
sys.path.append(os.getcwd() + "/lib")
import POSSolXml as posxml


class POSSolHttp:
    'Solace HTTP connection implementation'

    # --------------------------------------------------------------
    # Constructor
    # --------------------------------------------------------------
    def __init__(self, me, host, user, passwd, url='/SEMP'):
        self.m_logger = logging.getLogger(me)
        self.m_logger.enter("%s::%s : %s %s %s", __name__, inspect.stack()[0][3], host, user, url)

        self.m_me = me
        self.m_host = host
        self.m_user = user
        self.m_passwd = passwd
        self.m_url = url
        self.OpenHttpConnection()

    # -------------------------------------------------------
    # Connection related functions
    #
    def OpenHttpConnection(self):
        log = self.m_logger
        log.enter("%s::%s :", __name__, inspect.stack()[0][3])
        if sys.version_info[0] == 3:
            base64_str = base64.encodestring(('%s:%s' % (self.m_user, self.m_passwd)).encode()).decode().replace('\n', '')
            auth = base64_str.strip()
        else:
            auth = string.strip(base64.encodestring(self.m_user + ":" + self.m_passwd))
        log.debug ("auth: %s", auth)
        self.m_hdrs = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        self.m_hdrs["Authorization"] = "Basic %s" % auth
        log.info("HTTP connection to :%s", self.m_host)
        log.debug("Headers: %s", list(self.m_hdrs.items()))
        try:
            self.m_conn = http.HTTPConnection(self.m_host)
        except http.InvalidURL as e:
            log.exception(e)
            raise
        except:
            log.exception("Unexpected exception: %s", sys.exc_info()[0])
            raise
        log.debug("%s::%s : HTTP Connection open", __name__, inspect.stack()[0][3])
        return self.m_conn

    # -------------------------------------------------------
    # Post a req
    # TODO: Check Respose Status
    def Post(self, req):
        log = self.m_logger
        log.enter("%s::%s :", __name__, inspect.stack()[0][3])
        log.trace("request: %s", req)

        log.debug("URL: %s", self.m_url)
        self.m_conn.request("POST", self.m_url, req, self.m_hdrs)
        self.m_res = self.m_conn.getresponse()
        log.info("HTTP Response Status: %s Reason: %s", self.m_res.status, self.m_res.reason)
        if not self.m_res:
            raise Exception("No SEMP response")
        self.m_resp = self.m_res.read().decode(encoding="utf-8")
        log.debug("response data: %s", self.m_resp)
        if self.m_resp is None:
            raise Exception("Null SEMP response")
            return None
        return self.m_resp
