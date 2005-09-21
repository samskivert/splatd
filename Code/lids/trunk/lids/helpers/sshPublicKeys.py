# sshPublicKeys.py vi:ts=4:sw=4:expandtab:
#
# LDAP SSH Public Key Helper.
# Authors:
#       Will Barton <wbb4@opendarwin.org>
#       Landon Fuller <landonf@threerings.net>
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

import sys, os, logging

import lids
from lids import plugin

logger = logging.getLogger(lids.LOG_NAME)

# Sub-process result codes
SSH_ERR_NONE = 0
SSH_ERR_MISC = 1
SSH_ERR_PRIVSEP = 2
SSH_ERR_MKDIR = 3
SSH_ERR_WRITE = 4

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

        # Fork and setuid to write the files
        pipe = os.pipe()
        outf = os.fdopen(pipe[1], 'w')
        inf = os.fdopen(pipe[0], 'r')

        pid = os.fork()
        if (pid == 0):
            # Drop privs
            try:
                os.setgid(int(attributes.get("gidNumber")[0]))
                os.setuid(int(attributes.get("uidNumber")[0]))
            except OSError, e:
                print str(e)
                outf.write(str(e) + '\n')
                outf.close()
                os._exit(SSH_ERR_PRIVSEP)

            try:
                # Make sure the directory exists
                dir = os.path.split(filename)[0]
                if not os.path.exists(dir): os.makedirs(dir)
            except OSError, e:
                outf.write(str(e) + '\n')
                outf.close()
                os._exit(SSH_ERR_MKDIR)

            try:
                f = open(filename, "w+")
                f.write(contents)
                f.close()
            except IOError, e:
                outf.write(str(e) + '\n')
                outf.close()
                os._exit(SSH_ERR_WRITE)

            os._exit(SSH_ERR_NONE)
        else:
            while (1):
                try:
                    result = os.waitpid(pid, 0)
                except OSError, e:
                    import errno
                    if (e.errno == errno.EINTR):
                        continue
                    raise
                break

            status = os.WEXITSTATUS(result[1])

        errstr = inf.readline()
        outf.close()
        inf.close()

        # Handle the error conditions
        if (status == SSH_ERR_NONE):
            return

        if (status == SSH_ERR_PRIVSEP):
            raise plugin.LIDSPluginError, "Failed to drop privileges, %s" % errstr

        if (status == SSH_ERR_MKDIR):
            raise plugin.LIDSPluginError, "Failed to create SSH directory '%s', %s" % errstr

        if (status == SSH_ERR_WRITE):
            raise plugin.LIDSPluginError, "Failed to write SSH key, %s" % errstr


    # A list of modifyable attributes for this helper, 
    # for interactive modifications (i.e. web interface)
    def attributes(self, ldapEntry):
        """ Return the modifyable attribues and their current values """
        key = ldapEntry.attributes.get("sshPublicKey")
        return {'sshPublicKey':key,}

# Required Attributes
Writer.attributes = ('sshPublicKey', 'homeDirectory', 'gidNumber', 'uidNumber')
