MKDIR?=mkdir
RM?=rm
INSTALL?=install
PREFIX?=/opt/pipx/venvs/overlord
MANDIR?=${PREFIX}/share/man

all: install-overlord install-libexec install-manpages

install-overlord:
	pipx install --force --global -e .

install-libexec:
	${MKDIR} -m 755 -p "${DESTDIR}${PREFIX}/libexec/overlord"

	${INSTALL} -m 555 libexec/vm-install-from-components.sh "${DESTDIR}${PREFIX}/libexec/overlord/vm-install-from-components.sh"
	${INSTALL} -m 555 libexec/vm-install-from-appjail-image.sh "${DESTDIR}${PREFIX}/libexec/overlord/vm-install-from-appjail-image.sh"
	${INSTALL} -m 555 libexec/vm-start.sh "${DESTDIR}${PREFIX}/libexec/overlord/vm-start.sh"
	${INSTALL} -m 555 libexec/safe-exc.sh "${DESTDIR}${PREFIX}/libexec/overlord/safe-exc.sh"

install-manpages:
	${MKDIR} -m 755 -p "${DESTDIR}${MANDIR}/man1"
	${MKDIR} -m 755 -p "${DESTDIR}${MANDIR}/man5"

	${INSTALL} -m 444 man/man1/overlord.1 "${DESTDIR}${MANDIR}/man1/overlord.1"
	${INSTALL} -m 444 man/man5/overlord-spec.5 "${DESTDIR}${MANDIR}/overlord-spec.5"

uninstall: uninstall-overlord uninstall-libexec uninstall-manpages

uninstall-overlord:
	pipx uninstall --global overlord

uninstall-libexec:
	${RM} -f "${DESTDIR}${PREFIX}/libexec/overlord/vm-install-from-components.sh"
	${RM} -f "${DESTDIR}${PREFIX}/libexec/overlord/vm-install-from-appjail-image.sh"
	${RM} -f "${DESTDIR}${PREFIX}/libexec/overlord/vm-start.sh"
	${RM} -f "${DESTDIR}${PREFIX}/libexec/overlord/safe-exc.sh"

uninstall-manpages:
	${RM} -f "${DESTDIR}${MANDIR}/man1/overlord.1"
	${RM} -f "${DESTDIR}${MANDIR}/man5/overlord-spec.5"
