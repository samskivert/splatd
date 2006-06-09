# New ports collection makefile for:	py-splat
# Date created:		26 September 2005
# Whom:			Landon Fuller <landonf@opendarwin.org>
#
# $FreeBSD: $

PORTNAME=	splat
PORTVERSION=	1.0rc1
CATEGORIES=	net python
MASTER_SITES=	http://dpw.threerings.net/projects/splat/
DISTNAME=	${PORTNAME}-1.0-rc1

MAINTAINER=	landonf@opendarwin.org
COMMENT=	Splat is the Scalable Periodic LDAP Attribute Transmogrifier

BUILD_DEPENDS=	${PYTHON_SITELIBDIR}/ZConfig:${PORTSDIR}/devel/py-zconfig \
		${PYTHON_SITELIBDIR}/ldap:${PORTSDIR}/net/py-ldap2 \
		${PYTHON_SITELIBDIR}/twisted:${PORTSDIR}/devel/py-twistedCore
RUN_DEPENDS=	${BUILD_DEPENDS}

WRKSRC=		${WRKDIR}/${DISTNAME}

USE_PYTHON=	2.2+
USE_PYDISTUTILS=	yes
USE_RC_SUBR=	splatd.sh
SUB_LIST+=	PYTHON_CMD=${PYTHON_CMD}

post-install:
	${INSTALL_DATA} ${WRKSRC}/splat.conf ${LOCALBASE}/etc/splat.conf.sample
	${MV} -f ${LOCALBASE}/bin/splatd ${LOCALBASE}/sbin/splatd

.include <bsd.port.mk>
