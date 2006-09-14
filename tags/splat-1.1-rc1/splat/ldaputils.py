# ldaputils.py vi:ts=4:sw=4:expandtab:
#
# Splat LDAP support classes.
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

import ldap, ldap.modlist, ldap.sasl
import time

import splat
from splat import SplatError

class Connection(object):
    """
    Simple wrapper around an LDAP connection
    """
    def __init__(self, uri):
        """
        Initialize a new LDAP connection with the given URI and LDAP version
        @param uri: URI of LDAP server(s).
        """
        self._ldap = ldap.initialize(uri)
        self._ldap.protocol_version = ldap.VERSION3

    def simple_bind(self, bind_dn, password):
        """
        Initiate a simple_bind.
        @param bind_dn: Bind DN
        @param password: Bind Password
        """
        self._ldap.simple_bind_s(bind_dn, password)

    def gssapi_bind(self, authz_id=''):
        """
        Initiate a GSSAPI (Kerberos 5) SASL bind.
        @param authz_id: Kerberos principal. Omit to use your default principal.
        """
        self._ldap.sasl_interactive_bind_s('', ldap.sasl.gssapi(authz_id))

    def search(self, base_dn, scope, filter, attributes=None):
        """ 
        Search the given base DN of the given LDAP server within
        the given scope (defaulting to subtree), applying
        the given filter, and returns a list of Entry objects
        containing the results.
        @param base_dn: Search base DN.
        @param scope: Search scope. One of ldap.SCOPE_SUBTREE, ldap.SCOPE_BASE, or ldap.SCOPE_ONE
        @param filter: LDAP search filter.
        @param attributes: Attributes to return. None causes all attributes to be returned. Defaults to None.
        """
        # Search the directory using the given base and filter, if we get
        # results, put them in a list, and hand off to SearchResults
        result_id = self._ldap.search(base_dn, scope, filter, attributes)
        result_set = []
        while 1:
            result_type,result_data = self._ldap.result(result_id, 0)
            if result_data == []:
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data)
        result = []
        for entry in result_set:
            dn = entry[0][0]
            attrs = entry[0][1]
            result.append(Entry(dn, attrs))
        return result

    def modify(self, mod):
        """
        Thin wrapper around ldap.LDAPObject.modify_s()
        @param dn: Target DN
        @param mod: Modification instance
        """
        self._ldap.modify_s(mod.dn, mod.modlist)

class Entry(object):
    """
    LDAP Entry
    """
    def __init__(self, dn, attributes):
        """
        Initialize new entry with DN and attributes.
        """
        self.dn = dn
        self.attributes = attributes

class Modification(object):
    """
    LDAP Modification Description
    """
    def __init__(self, dn):
        """
        Initialize a new Modification object.
        @param dn: dn to modify
        """
        self.dn = dn
        self.modlist = []

    def add(self, attribute, value):
        """
        Add a new attribute with value(s).
        @param attribute: Attribute name.
        @param value: A string value, or a list of values.
        """
        self.modlist.append((ldap.MOD_ADD, attribute, value))

    def replace(self, attribute, value):
        """
        Replace an existing attribute value.
        @param attribute: Attribute name.
        @param value: A string value, or a list of values.
        """
        self.modlist.append((ldap.MOD_REPLACE, attribute, value))

    def delete(self, attribute, value=None):
        """
        Delete an existing attribute.
        @param attribute: Attribute name.
        @param value: A string value, a list of values, or None (delete all instances of attribute). Defaults to None.
        """
        self.modlist.append((ldap.MOD_DELETE, attribute, value))

class GroupFilter(object):
    """
    LDAP Group Filter Object
    """
    def __init__(self, baseDN, scope, filter, memberAttribute='uniqueMember'):
        """
        Initialize a new group filter object
        @param baseDN: LDAP search base
        @param scope: LDAP search scope
        @param filter: LDAP search filter
        @param memberAttribute: Attribute containing member DN. Defaults to 'uniqueMember'
        """
        self.baseDN = baseDN
        self.scope = scope
        self.filter = filter
        self.memberAttribute = memberAttribute
        # Default cache TTL in seconds
        self.cacheTTL = 30
        # Time of last update.
        self._lastUpdate = 0

    def isMember(self, ldapConnection, dn):
        """
        Verify that dn is a member of the group(s) returned by the LDAP search specified
        at instance initialization.
        @param ldapConnection: A valid LDAP Connection instance
        @param dn: DN to test against group list
        """
        if (time.time() - self._lastUpdate > self.cacheTTL or self._lastUpdate == 0):
            # If we've exceeded our cache TTL (or no previous search has
            # been performed), perform a new search.
            self.groups = ldapConnection.search(self.baseDN, self.scope, self.filter, [self.memberAttribute,])
            self._lastUpdate = time.time()

        for group in self.groups:
            attributes = group.attributes
            if (not attributes.has_key(self.memberAttribute)):
                continue
            
            for value in attributes[self.memberAttribute]:
                if (value == dn):
                    return True

        # DN not found, fall through.
        return False

