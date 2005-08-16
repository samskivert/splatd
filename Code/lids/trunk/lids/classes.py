# classes.py vi:ts=4:sw=4:expandtab:
#
# LIDS support classes.
# Author: Will Barton <wbb4@opendarwin.org>
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

import ldap

class LIDSError(Exception):
    pass

class SearchResult(list):
    """ """
    # The result looks like:
    #   [   List of entries
    #       [ ( entry, attributes ) ]
    #        [ ( entry, attributes ) ]

    result_set = []
    
    def __init__(self, result_set):
        self.result_set = result_set
        self.extract_entries()

    def extract_entries(self): 
        # Extract the entries from the result_set, and create Entrys
        # for them, added to self (which is a list object)
        for entry in self.result_set:
            dn = entry[0][0]
            attrs = entry[0][1]
            self.append(Entry(dn, attrs))

class Entry(dict):
    """ """

    def __init__(self, dn, attrs):
        self["dn"] = dn
        self.update(attrs)

    def dn(self):
        return self.get("dn", None)

    def getAttribute(self, attr):
        """ 
            Fetch an attribute's value from the entry.  If the entry
            value is a list, and there is only one item in the list, it
            will return just the item.
        """

        value = self.get(attr, None)

        ## XXX: need a more polymorphic way to check if the value is a
        ##      sequence
        if value.__class__ == list and len(value) == 1:
            value = value[0]

        return value

    def modification(self, mod_dict):
        l = []
        for attr in mod_dict:
            value = mod_dict[attr]
            
            action = ldap.MOD_REPLACE
        
            # If the entry doesn't already have this attribute, we need to
            # be adding, rather than modifying
            if not self.has_key(attr):
                action = ldap.MOD_ADD

            # If the value is our existing value, then we don't need to do
            # anything
            if value != self.get(attr, None):
                l.append((action, attr, value))

        # This is series of tupples in a list, formatted for the second 
        # argument to ldap.modify.  This class doesn't actually touch ldap.
        return l
            
    
class Object(object):
    def __init__(self): pass
    def work(self, ldapEntry):
        raise NotImplementedError, \
                "This method is not implemented in this abstract class"
    def modify(self, ldapEntry, modifyDict):
        raise NotImplementedError, \
                "This method is not implemented in this abstract class"
    def convert(self): pass
