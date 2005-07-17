# lidd.py
# LDAP Information Distribution Suite
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

import getopt, sys
import lids
import logging

if __name__ == "__main__":

    conf_file = None
    
    try:
        opts,args = getopt.getopt(sys.argv[1:], "hvf:")
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt,arg in opts:
        if opt == "-h":
            usage()
            sys.exit()
        if opt == "-f":
            conf_file = arg

    # Set up the configuration
    conf = lids.parse_config(conf_file)

    # Set up logging, based on the config file
    logfile = conf.get("daemon.logfile", "lids.log")
    loglevel = conf.get("daemon.loglevel", "info")

    # Set up logging
    if logfile:
        levels = {
                "debug":logging.DEBUG,
                "info":logging.INFO,
                "warning":logging.WARNING,
                "error":logging.ERROR,
                "critical":logging.CRITICAL,
                }

        # Get the lids logger
        logger = logging.getLogger("lids")
        logger.setLevel(levels[loglevel.lower()])

        formatter = logging.Formatter('%(asctime)s %(levelname)-6s %(message)s',
                '%Y%m%d %H:%M:%S')
        log = logging.FileHandler(logfile)
        log.setLevel(levels[loglevel.lower()])
        log.setFormatter(formatter)
        logger.addHandler(log)

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)
        logger.addHandler(console)
 

    # Run the daemon
    lids.daemon(conf)

