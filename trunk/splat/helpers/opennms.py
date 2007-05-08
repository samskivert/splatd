# opennms.py vi:ts=4:sw=4:expandtab:
#
# Support functions for plugins that deal with OpenNMS.
# Author: Landon Fuller <landonf@threerings.net>
#
# Copyright (c) 2007 Three Rings Design, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the copyright owner nor the names of contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import splat.plugin

try:
    # Python 2.5 cElementTree
    from xml.etree import cElementTree as ElementTree
except ImportError:
    # Stand-alone pre-2.5 cElementTree
    import cElementTree as ElementTree

# XML Namespaces
XML_USERS_NAMESPACE = "http://xmlns.opennms.org/xsd/users"
XML_GROUPS_NAMESPACE = "http://xmlns.opennms.org/xsd/groups"

class Users (object):
    def __init__ (self, path):
        self.doc = ElementTree.ElementTree(file = path)

    def findUser (self, username):
        for entry in self.doc.findall("./{%s}users/*" % (XML_USERS_NAMESPACE)):
            userId = entry.find("user-id")
            if (userId != None and userId.text == username):
                return entry

        # Not found
        return None

    @classmethod
    def _setChildElementText (self, parentNode, nodeName, text):
        node = parentNode.find(nodeName)
        node.text = text

    @classmethod
    def _setContactInfo (self, parentNode, contactType, info, serviceProvider = None):
        node = self._findUserContact(parentNode, contactType)

        node.set("info", info)
        if (serviceProvider != None):
            node.set("serviceProvider", serviceProvider)

    @classmethod
    def _findUserContact (self, parentNode, contactType):
        nodes = parentNode.findall("./{%s}contact" % (XML_USERS_NAMESPACE))
        for node in nodes:
            if (node.get("type") == contactType):
                return node

        return None

    def updateUser (self, user, fullName = None, comments = None, email = None,
        pagerEmail = None, xmppAddress = None, numericPager = None, textPager = None):
        """
        Update a user record.

        <user>
            <user-id xmlns="">admin</user-id>
            <full-name xmlns="">Administrator</full-name>
            <user-comments xmlns="">Default administrator, do not delete</user-comments>
            <password xmlns="">xxxx</password>
            <contact type="email" info=""/>
            <contact type="pagerEmail" info=""/>
            <contact type="xmppAddress" info=""/>
            <contact type="numericPage" info="" serviceProvider=""/>
            <contact type="textPage" info="" serviceProvider=""/>
        </user>

        @param user: User XML node to update.
        @param fullName: User's full name.
        @param comments: User comments.
        @param email: User's e-mail address.
        @param pagerEmail: User's pager e-mail address.
        @param xmppAddress: User's Jabber address.
        @param numericPager: User's numeric pager. (number, service) tuple.
        @param textPager: User's text pager. (number, service) tuple.
        """
        if (fullName != None):
            self._setChildElementText(user, "full-name", fullName)
        
        if (comments != None):
            self._setChildElementText(user, "user-comments", comments)

        if (email != None):
            self._setContactInfo(user, "email", email[0])

        if (pagerEmail != None):
            self._setContactInfo(user, "pagerEmail", pagerEmail[0], pagerEmail[1])

        if (xmppAddress != None):
            self._setContactInfo(user, "xmppAddress", xmppAddress[0])

        if (numericPager != None):
            self._setContactInfo(user, "numericPage", numericPager[0], numericPager[1])

        if (textPager != None):
            self._setContactInfo(user, "textPager", textPager[0], textPager[1])
