# New ports collection makefile for:	py-splat
# Date created:		26 September 2005
# Whom:			Landon Fuller <landonf@opendarwin.org>
#
# $FreeBSD: $

PORTNAME=	splat
PORTVERSION=	1.0beta5
CATEGORIES=	net python
MASTER_SITES=	http://dpw.threerings.net/projects/splat/
DISTNAME=	${PORTNAME}-1.0-beta5

MAINTAINER=	landonf@opendarwin.org
COMMENT=	LIDS is the LDAP Information Distribution System

BUILD_DEPENDS=	${PYTHON_SITELIBDIR}/ZConfig:${PORTSDIR}/devel/py-zconfig \
		${PYTHON_SITELIBDIR}/ldap:${PORTSDIR}/net/py-ldap2 \
		${PYTHON_SITELIBDIR}/twisted:${PORTSDIR}/devel/py-twistedCore
RUN_DEPENDS=	${BUILD_DEPENDS}

WRKSRC=		${WRKDIR}/${DISTNAME}

USE_PYTHON=	2.2+
USE_PYDISTUTILS=	yes
USE_RC_SUBR=	splat.sh
SUB_LIST+=	PYTHON_CMD=${PYTHON_CMD}

post-install:
	${INSTALL_DATA} ${WRKSRC}/splat.conf ${LOCALBASE}/etc/splat.conf.sample
	${MV} -f ${LOCALBASE}/bin/splatd ${LOCALBASE}/sbin/splatd

.include <bsd.port.mk>
