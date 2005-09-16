# sshPublicKeys.py vi:ts=4:sw=4:expandtab:
#
# LDAP SSH Public Key Helper.
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

__author__ = "Will Barton"

import sys, os, logging

import lids
from lids import plugin

logger = logging.getLogger(lids.LOG_NAME)

class Writer(plugin.Helper):
    def work(self, ldapEntry):
        attributes = ldapEntry.attributes

        # Test for required attributes
        if (not attributes.has_key('sshPublicKey') or not attributes.has_key('homeDirectory')):
            return
        if (not attributes.has_key('uidNumber') or not attributes.has_key('gidNumber')):
            return

        home = attributes.get("homeDirectory")[0]
        key = attributes.get("sshPublicKey")[0]
        # Grab the key type from the string, "ssh-rsa ..."
        key_type = key[4:7]

        filename = "%s/.ssh/id_%s.pub" % (home, key_type)
        contents = "%s" % key
    
        logger.info("Writing %s key to %s" % (key_type, filename))

        # Fork and seteuid to write the files
        if not os.fork():
            try:
                os.setgid(int(attributes.get("gidNumber")[0]))
                os.setuid(int(attributes.get("uidNumber")[0]))
            except OSError, e:
                raise plugin.LIDSPluginError, "Failed to drop privileges, %s" % e

            try:
                # Make sure the directory exists
                dir = os.path.split(filename)[0]
                if not os.path.exists(dir): os.makedirs(dir)
            except OSError, e:
                raise plugin.LIDSPluginError, "Failed to create SSH directory '%s', %s" % (dir, e)

            try:
                f = open(filename, "w+")
                f.write(contents)
                f.close()
            except IOError, e:
                raise plugin.LIDSPluginError, "Failed to write SSH key, %s" % (e)

            sys.exit()

        os.wait()

    # A list of modifyable attributes for this helper, 
    # for interactive modifications (i.e. web interface)
    def attributes(self, ldapEntry):
        """ Return the modifyable attribues and their current values """
        key = ldapEntry.attributes.get("sshPublicKey")
        return {'sshPublicKey':key,}

# Required Attributes
Writer.attributes = ('sshPublicKey', 'homeDirectory', 'gidNumber', 'uidNumber')
