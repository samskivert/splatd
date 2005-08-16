# functions.py vi:ts=4:sw=4:expandtab:
#
# LIDS support functions.
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

import os.path, logging
import ldap

import lids
import helpers
import classes
from lids.classes import LIDSError

def parse_config(conffile):
    """ 
        This function takes a configuration file, and returns a
        dictionary with the values, as 'section.option'.

        For example:
            [ldap]
            address: 10.10.10.1
        would be represented in the dictionary as
            conf["ldap.address"].
    """
    import ConfigParser
    logger = logging.getLogger("lids")

    if conffile == None or not os.path.exists(conffile):
        logger.critical("Configuration file %s doesn't exist" % conffile)
        raise ValueError, "Conf file is None or does not exist"

    config = ConfigParser.ConfigParser()
    config.read(conffile)

    confdict = {}
    logger.debug("Sorting config file sections and options")
    for section in config.sections():
        logger.debug("Adding options for section %s" % section)
        for option in config.options(section):
            confdict["%s.%s" % (section, option)] = config.get(section, option)

    return confdict

def _verify_server(server_address):
    """
        This function will verify the IP address or FQN of the server,
        and will raise a LIDSError if it is malformed of invalid in any
        way.
    """
    logger = logging.getLogger("lids")
    ## XXX: Implement
    logger.debug("Verifying server address")
    logger.debug("IMPLEMENT VERIFICATION OF SERVER ADDRESS")
    return server_address

def search(conf, section, base_dn=None, filter=None):
    """ 
        This function searches the given base DN of the given LDAP
        server within the given scope (defaulting to subtree), applying
        the given filter, and returning a SearchResult object
        containing the results.
    """
    logger = logging.getLogger("lids")
    server = conf["ldap.address"]
    
    if base_dn == None and filter == None:
        logger.debug("Using config file base_dn and filter to search %s" \
                % section)
        base_dn = conf[section + ".search_base"]
        filter = conf[section + ".search_filter"]

    ## XXX: Should this be arguments?
    scope = ldap.SCOPE_SUBTREE 
    retrieve_attrs = None
    protocol = ldap.VERSION3

    # Open the LDAP connection, catch the exception and throw our own,
    # if necessary
    try: 
        logger.debug("Connecting to LDAP server")
        l = ldap.open(_verify_server(server))
        l.protocol_version = protocol
    except ldap.LDAPError, e:
        logger.critical("An LDAPError occurred: %s" % e)
        raise LIDSError, "An LDAPError occurred: %s" % e
   
    # Search the directory using the given base and filter, if we get
    # results, put them in a list, and hand off to SearchResults
    try:
        logger.info("Searching LDAP with base DN: %s, filer: %s" \
                % (base_dn, filter))
        result_id = l.search(base_dn, scope, filter, retrieve_attrs)
        result_set = []
        while 1:
            result_type,result_data = l.result(result_id, 0)
            if result_data == []:
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data)
        return classes.SearchResult(result_set)
    except ldap.LDAPError, e:
        logger.critical("An LDAPError occurred: %s" % e)
        raise LIDSError, "An LDAPError occurred: %s, %s, %s" % \
                (e, base_dn, filter)

    return None
   
def bind(conf, bind_dn, password):
    logger = logging.getLogger("lids")
    server = conf["ldap.address"]

    try:
        logger.debug("Connceting to ldap")
        l = ldap.open(server)
        l.simple_bind(bind_dn, password)
    except ldap.LDAPError, e:
        logger.critical("An LDAPError occurred: %s" % e)
        raise LIDSError, "An LDAPError occurred: %s" % e

def modify(conf, entry_dn, mod_dict, bind_dn = None, password = None):
    logger = logging.getLogger("lids")
    server = conf["ldap.address"]

    if not bind_dn:
        bind_dn = conf["ldap.bind_dn"]
    if not password:
        password = conf["ldap.password"]

    # First, we need to grab the existing entry
    # XXX: Perhaps some cachign or something, so that we don't have to
    # query LDAP here
    entry = search(conf, None, entry_dn, "objectclass=*")[0]
    modification = entry.modification(mod_dict)
    
    logger.debug("Modification to entry %s: %s" \
            % (entry_dn, str(modification)))

    try:
        logger.debug("Connceting to ldap")
        l = ldap.open(server)
        l.simple_bind(bind_dn, password)
    except ldap.LDAPError, e:
        logger.critical("An LDAPError occurred: %s" % e)
        raise LIDSError, "An LDAPError occurred: %s" % e

    logger.info("Modifying %s" % entry_dn)
    l.modify_s(entry_dn, modification)


def push(conf, section):
    logger = logging.getLogger("lids")

    hclass = get_helper(conf, section)
    helper = hclass()

    searchResult = search(conf, section)

    for e in searchResult:
        logger.debug("Calling the helper's work method for %s" % e["dn"])
        helper.work(e)

def get_helper(conf, section):
    logger = logging.getLogger("lids")

    # Get the helper name, this should be module.class
    helpername = conf[section + ".helper"]

    # The module name, extracted from the helpername
    helper_module = helpername.split(".")[0]
    helper_class = helpername.split(".")[1]

    # Get the class object (not an instance)
    try:
        # We assume that the module has already been loaded, through the
        # lids.helper.__init__ script
        #
        # XXX: Don't assume this, helpers shouldn't be required to be
        # part of the lids package
        hclass = helpers.__dict__[helper_module].__dict__[helper_class]
    except KeyError:
        logger.critical("Unable to find the helper module or class")
        logger.critical("Module: %s, Class: %s" \
                % (helper_module, helper_class))
        sys.exit(1)

    return hclass

def helper_attributes(conf, section, entry):
    logger = logging.getLogger("lids")
    hclass = get_helper(conf, section)
    helper = hclass()
    a = helper.attributes(entry)
    return a


