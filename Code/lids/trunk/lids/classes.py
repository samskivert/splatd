# Copyright (c) 2005 Three Rings Design, Inc.
# All Rights Reserved.
# 
# Author: Will Barton
#
# lids - LDAP Information Distribution System
# A library for retrieving, formatting, and updating information stored in 
# an LDAP database
#
# This file contains support classes for the LIDS.
#

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
