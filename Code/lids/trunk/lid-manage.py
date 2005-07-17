#!/usr/bin/env python
#
# lid-manage.py
# A tool for managing SSH keys stored in LDAP
# LDAP Information Distribution Suite
#
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

import sys, logging
import lids

def search(conf, section):
    l = lids.search(conf, section)
    for e in l:
        print e.getAttribute("dn")
        print e.getAttribute("uid")
    
def usage():
    print "%s: [-v] [-s search section] [-f config file]" % sys.argv[0]

def push(conf, section):
    lids.push(conf, section)

def modify(conf, base_dn, modlist):
    mod_dict = {}
    for mod in modlist:
        attr,value = mod.split("=",1)
        mod_dict[attr] = value
    lids.modify(conf, base_dn, mod_dict)

if __name__ == "__main__":
    import getopt

    action = None
    section = None
    base_dn = None
    modlist = []
    conf_file = None
    conf = {}

    try:
        opts,args = getopt.getopt(sys.argv[1:], "hvs:f:p:d:m:")
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt,arg in opts:
        if opt == "-h":
            usage()
            sys.exit()
        if opt == "-v": 
            pass
        if opt == "-s": 
            action = "search"
            section = arg
        if opt == "-f":
            conf_file = arg
        if opt == "-p":
            action = "push"
            section = arg
        if opt == "-d":
            base_dn = arg
        if opt == "-m":
            action = "modify"
            modlist.append(arg)

    logger = logging.getLogger("lids")
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)-6s %(message)s',
            '%Y%m%d %H:%M:%S')
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)
 
    try:
        # Set up the configuration
        conf = lids.parse_config(conf_file)
    except ValueError:
        usage()
        sys.exit(1)

    if action == "search":
        search(conf, section)
    elif action == "push":
        push(conf, section)
    elif action == "modify" and base_dn:
        modify(conf, base_dn, modlist)
    else:
        usage()
        sys.exit(2)

