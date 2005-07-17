# Copyright (c) 2005 Three Rings Design, Inc.
# All Rights Reserved.
# 
# Author: Will Barton
#
# lids - LDAP Information Distribution System
# A library for retrieving, formatting, and updating information stored in 
# an LDAP database
#

__author__ = "Will Barton"

import sys, os, logging

import lids.classes
import lids.functions

logger = logging.getLogger("lids")

class Writer(lids.classes.Object):

    def __init__(self): pass
    
    def work(self, ldapEntry):
        home = ldapEntry.getAttribute("homeDirectory")
        key = ldapEntry.getAttribute("sshPublicKey")
        # Grab the key type from the string, "ssh-rsa ..."
        key_type = key[4:7]

        filename = "%s/.ssh/id_%s.pub" % (home, key_type)
        contents = "%s" % key
    
        logger.info("Writing %s key to %s" % (key_type, filename))

        # Fork and seteuid to write the files
        if not os.fork():
            os.setgid(int(ldapEntry.getAttribute("gidNumber")))
            os.setuid(int(ldapEntry.getAttribute("uidNumber")))

            # Make sure the directory exists
            dir = os.path.split(filename)[0]
            if not os.path.exists(dir): os.makedirs(dir)

            f = open(filename, "w+")
            f.write(contents)
            f.close()
            sys.exit()

        os.wait()

    # A list of modifyable attributes for this helper, 
    # for interactive modifications (i.e. web interface)
    def attributes(self, ldapEntry):
        """ Return the modifyable attribues and their current values """
        key = ldapEntry.getAttribute("sshPublicKey")
        return {'sshPublicKey':key,}
