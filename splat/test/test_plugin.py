#!/usr/bin/env python
# test_plugin.py vi:ts=4:sw=4:expandtab:
#
# Scalable Periodic LDAP Attribute Transmogrifier
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

from splat import plugin

from splat.ldaputils import client as ldapclient
from splat.ldaputils.test import slapd

import ldap, time

# Useful Constants
from splat.test import DATA_DIR

# Mock Helper
class MockHelper(plugin.Helper):
    # Last instance work success flag and context. This is obviously
    # not safe outside of testing
    success = None
    context = None

    def __init__(self):
        MockHelper.success = False
        self.lastRun = 0

    @classmethod
    def attributes(self):
        return ('dn',)

    @classmethod
    def parseOptions(self, options):
        assert(options['test'] == 'value')
        return options

    def work(self, context, ldapEntry, modified):
        assert(context['test'] == 'value')
        assert(ldapEntry.dn == 'uid=john,ou=People,dc=example,dc=com')
        assert(ldapEntry.attributes.has_key('modifyTimestamp'))
        # Independently verify the modify time stamp
        entryMod = time.mktime(time.strptime(ldapEntry.attributes['modifyTimestamp'][0] + 'UTC', "%Y%m%d%H%M%SZ%Z")) - time.timezone
        if (entryMod >= self.lastRun):
            assert(modified)
        else:
            assert(not modified)

        MockHelper.context = context
        MockHelper.success = True

        self.lastRun = int(time.time())

# Test Cases
class HelperWithControllerTestCase(unittest.TestCase):
    """ Test Splat Helper """

    def setUp(self):
        self.slapd = slapd.LDAPServer()
        self.conn = ldapclient.Connection(slapd.SLAPD_URI)

        options = {'test':'value'}
        self.hc = plugin.HelperController('test', 'splat.test.test_plugin', 5, 'dc=example,dc=com', '(uid=john)', False, options)

        MockHelper.context = None
        MockHelper.success = False

    def tearDown(self):
        self.slapd.stop()

    def test_work(self):
        # Test a new, unmodified entry
        self.hc.work(self.conn)

        # Try it again, without bumping the modTimestamp
        self.hc.work(self.conn)

        # Up the modTimestamp
        # Acquire write privs
        self.conn.simple_bind(slapd.ROOTDN, slapd.ROOTPW)

        # Find entry and modify it
        entry = self.conn.search(slapd.BASEDN, ldap.SCOPE_SUBTREE, '(uid=john)', None)[0]
        mod = ldapclient.Modification(entry.dn)
        mod.replace('description', 'Up the date')
        self.conn.modify(mod)

        # Test with the upped mod date
        self.hc.work(self.conn)

    def test_requireGroup(self):
        self.hc.requireGroup = True
        # Ensure that the worker is not called if requireGroup is True
        # and no groups have been added
        self.hc.work(self.conn)
        self.assertEquals(MockHelper.success, False)

    def test_requireGroupDisabled(self):
        # Ensure that the worker is called if requireGroup is False (default)
        # and no groups have been added
        self.hc.work(self.conn)
        self.assertEquals(MockHelper.success, True)

    def test_requireGroupNoMatch(self):
        self.hc.requireGroup = True
        # Add a group that will not match, and again ensure that the worker
        # is not called
        filter = ldapclient.GroupFilter(slapd.BASEDN, ldap.SCOPE_SUBTREE, '(&(objectClass=groupOfUniqueNames)(cn=administrators))', 'uniqueMember')
        self.hc.addGroup(filter, {'test':'value', 'group':'administrators'})
        self.hc.work(self.conn)
        self.assertEquals(MockHelper.success, False)

    def test_addGroup(self):
        self.hc.requireGroup = True
        # Add a group that will match. Ensure that the worker is called with the
        # correct context
        filter = ldapclient.GroupFilter(slapd.BASEDN, ldap.SCOPE_SUBTREE, '(&(objectClass=groupOfUniqueNames)(cn=developers))', 'uniqueMember')
        self.hc.addGroup(filter, {'test':'value', 'group':'developers'})
        self.hc.work(self.conn)
        self.assertEquals(MockHelper.success, True)
        self.assertEquals(MockHelper.context['group'], 'developers')

        # Add an additional group. Ensure that only the first group matches
        filter = ldapclient.GroupFilter(slapd.BASEDN, ldap.SCOPE_SUBTREE, '(&(objectClass=groupOfUniqueNames)(cn=developers))', 'uniqueMember')
        self.hc.addGroup(filter, {'test':'value', 'group':'developers2'})
        self.hc.work(self.conn)
        self.assertEquals(MockHelper.success, True)
        self.assertEquals(MockHelper.context['group'], 'developers')
