# homeDirectory.py vi:ts=4:sw=4:expandtab:
#
# XXX put copyright / license here

import os, logging

import splat
from splat import plugin

logger = logging.getLogger(splat.LOG_NAME)

# XXX need post-create script.

class WriterContext(object):
    """ Option Context """
    def __init__(self):
        self.minuid = None
        self.mingid = None
        self.home = None
        self.splitHome = None
        self.skelDirs = ('/usr/share/skel') # Default skeletal home directory

class Writer(plugin.Helper):
    # Required Attributes
    attributes = ('homeDirectory', 'gidNumber', 'uidNumber')

    # Recursively copy a directory tree, preserving permission modes and access
    # times, but changing ownership of files to uid:gid. Also, renames
    # files/directories named dot.foo to .foo.
    def __copySkelDir(srcDir, destDir, uid, gid):
        import re, shutil
        # Regular expression matching files named dot.foo
        pattern = re.compile('^dot\.')
        for srcFile in os.listdir(srcDir):
            destFile = pattern.sub('.', srcFile)
            # Not portable: hardcoded / as path delimeter
            srcPath = srcDir + '/' + srcFile
            destPath = destDir + '/' + destFile

            # Go deeper if we are copying a sub directory
            if (os.path.isdir(srcPath)):
                try:
                    os.makedirs(destPath)
                except OSError, e:
                    raise plugin.SplatPluginError, "Failed to create destination directory: %s" % destPath
                    continue
                
                __copySkelDir(srcPath, destPath, uid, gid)
            
            # Copy regular files
            else:
                try:
                    shutil.copy2(srcPath, destPath)
                except IOError, e: 
                    raise plugin.SplatPluginError, "Failed to copy %s to %s: %s" % (srcPath, destPath, e)
                    continue

            # Change ownership of files/directories after copied
            try:
                os.chown(destPath, uid, gid)
            except OSError, e:
                raise plugin.SplatPluginError, "Failed to change ownership of %s to %d:%d" % (destPath, uid, gid)
                continue
            

    def parseOptions(self, options):
        context = WriterContext()

        for key in options.keys():
            if (key == 'home'):
                context.home = os.path.abspath(options[key])
                splitHome = context.home.split('/')
                if (splitHome[0] != ''):
                    raise plugin.SplatPluginError, "Relative paths for the home option are not permitted"
                context.splitHome = splitHome
                continue
            if (key == 'minuid'):
                context.minuid = int(options[key])
                continue
            if (key == 'mingid'):
                context.mingid = int(options[key])
                continue
            if (key == 'skelDirs'):
                context.skelDirs = int(options[key])
                continue
            raise plugin.SplatPluginError, "Invalid option '%s' specified." % key

        return context

    def work(self, context, ldapEntry):
        attributes = ldapEntry.attributes

        # Test for required attributes
        if (not attributes.has_key('homeDirectory')):
            return
        if (not attributes.has_key('uidNumber') or not attributes.has_key('gidNumber')):
            return

        home = attributes.get("homeDirectory")[0]
        uid = int(attributes.get("uidNumber")[0])
        gid = int(attributes.get("gidNumber")[0])

        # Validate the home directory
        if (context.home != None):
            givenPath = os.path.abspath(home).split('/')
            if (len(givenPath) < len(context.splitHome)):
                raise plugin.SplatPluginError, "LDAP Server returned home directory (%s) located outside of %s for entry '%s'" % (home, context.home, ldapEntry.dn)

            for i in range(0, len(context.splitHome)):
                if (context.splitHome[i] != givenPath[i]):
                    raise plugin.SplatPluginError, "LDAP Server returned home directory (%s) located outside of %s for entry '%s'" % (home, context.home, ldapEntry.dn)

        # Validate the UID
        if (context.minuid != None):
            if (context.minuid > uid):
                raise plugin.SplatPluginError, "LDAP Server returned uid %d less than specified minimum uid of %d for entry '%s'" % (uid, context.minuid, ldapEntry.dn)
        # Validate the GID
        if (context.mingid != None):
            if (context.mingid > gid):
                raise plugin.SplatPluginError, "LDAP Server returned gid %d less than specified minimum gid of %d for entry '%s'" % (gid, context.mingid, ldapEntry.dn)

        # Validate skel directory
        for dir in context.skelDirs:
            if (not os.path.isdir(dir)):
                raise plugin.SplatPluginError, "Skeletal home directory %s does not exist or is not a directory" % dir

        # Create the home directory, unless it already exists
        if (not os.path.isdir(home)):
            try:
                os.makedirs(home)
                os.chown(home, uid, gid)
            except OSError, e:
                raise plugin.SplatPluginError, "Failed to create home directory, %s" % e
        # If it does already exist, do nothing at all and we are done
        else:
            return

        # Copy files from skeletal directories to user's home directory
        for dir in context.skelDirs:
            __copySkelDir(dir, home, uid, gid)
