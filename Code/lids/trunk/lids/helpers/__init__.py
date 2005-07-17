# Copyright (c) 2005 Three Rings Design, Inc.
# All Rights Reserved.
# 
# Author: Will Barton
#
# lids - LDAP Information Distribution System
# A library for retrieving, formatting, and updating information stored in 
# an LDAP database
#

import os
import re

# Import each of the appropriate helper modules in the directory
pyre = re.compile(".py$")
initre = re.compile("^__init__")

for f in os.listdir(__path__[0]):
    if pyre.search(f) and not initre.search(f):
        m = f.rsplit(".", 1)[0]
        __import__(m, globals(), locals(), [])

        
