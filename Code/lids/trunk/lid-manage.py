#!/usr/bin/env python
# Copyright (c) 2005 Three Rings Design, Inc.
# All Rights Reserved.
# 
# Author: Will Barton
#
# skd-manage
# A tool for managing SSH keys stored in LDAP
#

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

