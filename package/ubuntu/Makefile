# Fetch splat source, extract, add debian subdirectory, and build source and
# binary .deb packages. 

VERSION=	1.0
URL=		http://dpw.threerings.net/projects/splat/
SRC=		splat-$(VERSION).tar.gz
KEYID=		01ACE113

all:	pkg

fetch: fetch-stamp
fetch-stamp:
	wget $(URL)$(SRC)
	wget $(URL)$(SRC).sig
	gpg --verify $(SRC).sig
	touch fetch-stamp

clean:
	rm -rf splat* *-stamp

debdir:	debdir-stamp
debdir-stamp: fetch-stamp
	tar zxf $(SRC)
	mv $(SRC) splatd_$(VERSION).orig.tar.gz
	rsync -a --exclude .svn debian splat-$(VERSION)
	touch debdir-stamp

pkg:	pkg-stamp
pkg-stamp: debdir-stamp
	cd splat-$(VERSION) && dpkg-buildpackage -rfakeroot -uc -us -S -sa && cd ..
	touch pkg-stamp

sign:	sign-stamp
sign-stamp:	pkg-stamp
	debsign -k$(KEYID) splatd_*.changes

check: pkg-stamp
	lintian splatd_*.changes
	linda splatd_*.changes
