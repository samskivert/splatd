#!/usr/bin/env python
# test_plugin.py vi:ts=4:sw=4:expandtab:
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

from lids import plugin, ldaputils
import ldap
from lids.test import slapd

# Useful Constants
from lids.test import DATA_DIR

# Mock Helper
class MockHelper(plugin.Helper):
    def setOptions(self, options):
        assert(options['test'] == 'value')

    def work(self, ldapEntry):
        return True

    def modify(self, ldapEntry, modifyList):
        pass

    def convert(self):
        pass

MockHelper.attributes = ('dn',)

# Test Cases
class HelperWithControllerTestCase(unittest.TestCase):
    """ Test LIDS Helper """

    def setUp(self):
        options = {'test':'value'}
        self.hc = plugin.HelperController('lids.test.test_plugin', 5, 'dc=example,dc=com', '(uid=john)', None, None, options)

    def test_work(self):
        self.assert_(self.hc.work(None))


class GroupFilterTestCase(unittest.TestCase):
    """ Test Group Filters """
    def setUp(self):
        self.slapd = slapd.LDAPServer()
        self.conn = ldaputils.Connection(slapd.SLAPD_URI)
        self.entry = self.conn.search(slapd.BASEDN, ldap.SCOPE_SUBTREE, '(uid=john)')[0]

    def tearDown(self):
        self.slapd.stop()

    def test_isMember(self):
        filter = plugin.GroupFilter(self.conn, slapd.BASEDN, ldap.SCOPE_SUBTREE, '(&(objectClass=groupOfUniqueNames)(cn=developers))', 'uniqueMember')
        self.assert_(filter.isMember(self.entry.dn))

        filter = plugin.GroupFilter(self.conn, slapd.BASEDN, ldap.SCOPE_SUBTREE, '(&(objectClass=groupOfUniqueNames)(cn=administrators))', 'uniqueMember')
        self.assert_(not filter.isMember(self.entry.dn))

    def test_caching(self):
        filter = plugin.GroupFilter(self.conn, slapd.BASEDN, ldap.SCOPE_SUBTREE, '(&(objectClass=groupOfUniqueNames)(cn=developers))', 'uniqueMember')

        # Set a silly cache TTL to ensure it will never expire
        filter.cacheTTL = 3000000
        self.assert_(filter.isMember(self.entry.dn))

        # Acquire write privs
        self.conn.simple_bind(slapd.ROOTDN, slapd.ROOTPW)

        # Drop self.entry.dn from the developers group
        group = self.conn.search(slapd.BASEDN, ldap.SCOPE_SUBTREE, '(&(objectClass=groupOfUniqueNames)(cn=developers))')[0]
        mod = ldaputils.Modification(group.dn)
        mod.delete('uniqueMember', self.entry.dn)
        self.conn.modify(mod)

        # Verify that the group filter is still using the cached results
        self.assert_(filter.isMember(self.entry.dn))

        # Drop the cache TTL to force the filter to update its cache and
        # then verify that the cache has been updated
        filter.cacheTTL = 0
        self.assert_(not filter.isMember(self.entry.dn))
