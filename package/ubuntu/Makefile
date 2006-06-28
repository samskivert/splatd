# Fetch splat source, extract, add debian subdirectory, and build source and
# binary .deb packages. 

VERSION=	1.0
URL=		http://dpw.threerings.net/projects/splat/
SRC=		splat-$(VERSION).tar.gz
KEYID=		01ACE113

all:	pkg

fetch:
	wget $(URL)$(SRC)
	wget $(URL)$(SRC).sig
	gpg --verify $(SRC).sig
	touch fetch-stamp

clean:
	rm -rf splat* *-stamp
	
debianize: fetch-stamp
	tar zxf $(SRC)
	mv $(SRC) splatd_$(VERSION).orig.tar.gz
	svn export debian splat-$(VERSION)/debian
	touch debdir-stamp

pkg: debdir-stamp
	cd splat-$(VERSION); dpkg-buildpackage -rfakeroot -k$(KEYID)
	touch pkg-stamp

check: pkg-stamp
	lintian splatd_*.changes
	linda splatd_*.changes
