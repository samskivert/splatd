#!/bin/sh
# 
# Adapted from
# http://jpkg-library.googlecode.com/svn-history/r651/bin/create_release.sh by
# Jonathan LePlastrier
#

# Check the arguments
VERSION=$1
if [ -z $VERSION ]; then
    echo "Version must be set."
    exit 1
fi

TRUNK="trunk/"
TAG="tags/splatd-$VERSION"

# Be sure the checkout is up to date
svn up $TRUNK 
if [ $? -ne 0 ]; then
    echo "SVN updating failed, aborting tagging process."
    exit 1
fi

# Verify the tag is new
if [ -d $TAG ]; then
    echo "Tag $TAG already exists, aborting."
    exit 1
fi

# Make sure splat.__version__ matches the tag we are making
version_var=`grep __version__ $TRUNK/splat/__init__.py | cut -f2 -d\'`
if [ $version_var != $VERSION ]; then
    echo "splat.__version__ does not match $VERSION. Aborting tagging process."
    exit 1
fi

# Run unit tests
pushd .
cd $TRUNK
trial splat
popd

# Ensure tests succeed
if [ $? -ne 0 ]; then
    echo "Not all tests succeeded. Aborting release."
    exit 1
fi

# Create the tag
svn cp $TRUNK $TAG 
if [ $? -ne 0 ]; then
    echo "Creating the tag failed, aborting tagging process."
    exit 1
fi

# Build xhtml and man page documentation. This PREFIX is for Mac OS systems that
# have docbook-xml and docbook-xsl installed in /opt/local by MacPorts. Will
# probably need to be changed for other operating systems.
pushd .
cd $TAG/docs
env PREFIX=/opt/local make

if [ $? -ne 0 ]; then
    echo "Building documentation failed. Aborting release."
    exit 1
fi

# Back down to the root
popd

# Add the manual and man pages to tag so it can be served from SVN on Google
svn add $TAG/docs/man
svn add $TAG/docs/xhtml

# Fix up the svn mimetypes for the html [needed by Google code]
find $TAG/docs/xhtml -name \*.html -exec svn propset svn:mime-type text/html {} \;

svn commit -m "Created $TAG from trunk for release $VERSION." $TAG
