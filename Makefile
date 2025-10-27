MKDIR?=mkdir
RM?=rm
SED?=sed
INSTALL?=install
PREFIX?=/opt/pipx/venvs/overlord
MANDIR?=${PREFIX}/share/man
PIPX_INSTALL_FLAGS=

.if defined(SYSTEM_SITE_PACKAGES)
PIPX_INSTALL_FLAGS+=--system-site-packages
.endif

.if !defined(NOEDITABLE)
PIPX_INSTALL_FLAGS+=-e
.endif

all: install-overlord install-libexec install-manpages install-files

install-overlord:
	pipx install ${PIPX_INSTALL_FLAGS} --force --global .

install-libexec:
	${MKDIR} -m 755 -p "${DESTDIR}${PREFIX}/libexec/overlord"

	${INSTALL} -m 555 libexec/vm-install-from-components.sh "${DESTDIR}${PREFIX}/libexec/overlord/vm-install-from-components.sh"
	${INSTALL} -m 555 libexec/vm-install-from-appjail-image.sh "${DESTDIR}${PREFIX}/libexec/overlord/vm-install-from-appjail-image.sh"
	${INSTALL} -m 555 libexec/vm-install-from-pkgbase.sh "${DESTDIR}${PREFIX}/libexec/overlord/vm-install-from-pkgbase.sh"

	${SED} -i "" -e "s|%%PREFIX%%|${PREFIX}|g" "${DESTDIR}${PREFIX}/libexec/overlord/vm-install-from-pkgbase.sh"

	${INSTALL} -m 555 libexec/vm-start.sh "${DESTDIR}${PREFIX}/libexec/overlord/vm-start.sh"
	${INSTALL} -m 555 libexec/safe-exc.sh "${DESTDIR}${PREFIX}/libexec/overlord/safe-exc.sh"
	${INSTALL} -m 555 libexec/create.py "${DESTDIR}${PREFIX}/libexec/overlord/create.py"

install-manpages:
	${MKDIR} -m 755 -p "${DESTDIR}${MANDIR}/man1"
	${MKDIR} -m 755 -p "${DESTDIR}${MANDIR}/man5"

	${INSTALL} -m 444 man/man1/overlord.1 "${DESTDIR}${MANDIR}/man1/overlord.1"
	${INSTALL} -m 444 man/man5/overlord-spec.5 "${DESTDIR}${MANDIR}/man5/overlord-spec.5"

	${SED} -i "" -e "s|%%PREFIX%%|${PREFIX}|g" "${DESTDIR}${MANDIR}/man5/overlord-spec.5"

install-files:
	${MKDIR} -m 755 -p "${DESTDIR}${PREFIX}/share/overlord/files"
	${MKDIR} -m 755 -p "${DESTDIR}${PREFIX}/share/overlord/files/pkgbase"

	${INSTALL} -m 444 files/pkgbase/base.conf "${DESTDIR}${PREFIX}/share/overlord/files/pkgbase"

uninstall: uninstall-overlord uninstall-libexec uninstall-manpages uninstall-files

uninstall-overlord:
	pipx uninstall --global overlord

uninstall-libexec:
	${RM} -f "${DESTDIR}${PREFIX}/libexec/overlord/vm-install-from-components.sh"
	${RM} -f "${DESTDIR}${PREFIX}/libexec/overlord/vm-install-from-appjail-image.sh"
	${RM} -f "${DESTDIR}${PREFIX}/libexec/overlord/vm-install-from-pkgbase.sh"
	${RM} -f "${DESTDIR}${PREFIX}/libexec/overlord/vm-start.sh"
	${RM} -f "${DESTDIR}${PREFIX}/libexec/overlord/safe-exc.sh"
	${RM} -f "${DESTDIR}${PREFIX}/libexec/overlord/create.py"

uninstall-manpages:
	${RM} -f "${DESTDIR}${MANDIR}/man1/overlord.1"
	${RM} -f "${DESTDIR}${MANDIR}/man5/overlord-spec.5"

uninstall-files:
	${RM} -rf "${DESTDIR}${PREFIX}/share/overlord"
