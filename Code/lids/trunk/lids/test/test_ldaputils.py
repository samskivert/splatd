#!/usr/bin/env python
# test_ldap.py vi:ts=4:sw=4:expandtab:
#
# LDAP Information Distribution System
# Authors:
#       Landon Fuller <landonf@threerings.net>
#       Will Barton <wbb4@opendarwin.org>
#
# Copyright (c) 2005 Three Rings Design, Inc.
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

""" LDAP Unit Tests """

from twisted.trial import unittest
import ldap

from lids import ldaputils

# Useful Constants
from lids.test import DATA_DIR
from lids.test import slapd

# Test Cases
class ConnectionTestCase(unittest.TestCase):
    """ Test LDAP Connection """
    def setUp(self):
        self.slapd = slapd.LDAPServer()
        self.conn = ldaputils.Connection(slapd.SLAPD_URI)

    def tearDown(self):
        self.slapd.stop()

    def test_initialize(self):
        self.assertEquals(self.conn._ldap.protocol_version, ldap.VERSION3)

    def test_simple_bind(self):
        self.conn.simple_bind(slapd.ROOTDN, slapd.ROOTPW)

    def test_search(self):
        result = self.conn.search(slapd.BASEDN, ldap.SCOPE_SUBTREE, '(uid=john)', ['uid',])
        self.assertEquals(result[0].attributes['uid'][0], 'john')

    def test_modify(self):
        # Acquire write privs
        self.conn.simple_bind(slapd.ROOTDN, slapd.ROOTPW)

        # Find entry
        entry = self.conn.search(slapd.BASEDN, ldap.SCOPE_SUBTREE, '(uid=john)', None)[0]

        mod = {}
        mod.update(entry.attributes)
        # Test MOD_REPLACE
        mod['cn'] = "Test"
        # Test MOD_ADD
        mod['street'] = "Test"
        # Test MOD_DELETE
        mod.pop('loginShell')
        # Do modification
        self.conn.modify(entry.dn, entry.attributes, mod)

        # Verify the result
        entry = self.conn.search(slapd.BASEDN, ldap.SCOPE_SUBTREE, '(uid=john)', ['cn', 'street'])[0]
        self.assertEquals(entry.attributes.get('cn')[0], 'Test')
        self.assertEquals(entry.attributes.get('street')[0], 'Test')
        self.assert_(not entry.attributes.has_key('loginShell'))

class EntryTestCase(unittest.TestCase):
    """ Test LDAP Entry Objects """
    def setUp(self):
        self.slapd = slapd.LDAPServer()
        self.conn = ldaputils.Connection(slapd.SLAPD_URI)

    def tearDown(self):
        self.slapd.stop()

    def test_search_result(self):
        result = self.conn.search(slapd.BASEDN, ldap.SCOPE_SUBTREE, '(uid=john)', ['uid',])
        self.assertEquals(result[0].attributes['uid'][0], 'john')
        self.assertEquals(result[0].dn, 'uid=john,ou=People,dc=example,dc=com')
