#!/bin/bash
#
# Copyright (C) 2010-2021 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

export DEBIAN_FRONTEND=noninteractive

UPDATER_LOG="/var/log/univention/updater.log"
exec 3>>"$UPDATER_LOG"
UPDATE_NEXT_VERSION="$1"

die () {
	echo "$*" >&2
	exit 1
}
install () {
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir -y --force-yes install "$@" >&3 2>&3
}
reinstall () {
	install --reinstall "$@"
}
check_and_install () {
	local state
	state="$(dpkg --get-selections "$1" 2>/dev/null | awk '{print $2}')"
	if [ "$state" = "install" ]; then
		install "$1"
	fi
}
check_and_reinstall () {
	local state
	state="$(dpkg --get-selections "$1" 2>/dev/null | awk '{print $2}')"
	if [ "$state" = "install" ]; then
		reinstall "$1"
	fi
}
is_installed () {
	local state
	state="$(dpkg --get-selections "$1" 2>/dev/null | awk '{print $2}')"
	test "$state" = "install"
}
is_deinstalled() {
	local state
	state="$(dpkg --get-selections "$1" 2>/dev/null | awk '{print $2}')"
	test "$state" = "deinstall"
}

echo -n "Running postup.sh script:"
echo >&3
date >&3 2>&3

eval "$(univention-config-registry shell)" >&3 2>&3
# shellcheck source=/dev/null
. /usr/share/univention-lib/ucr.sh || exit $?

case "${server_role:-}" in
domaincontroller_master) install univention-server-master ;;
domaincontroller_backup) install univention-server-backup ;;
domaincontroller_slave) install univention-server-slave ;;
memberserver) install univention-server-member ;;
'') ;;  # unconfigured
basesystem) die "The server role '$server_role' is not supported anymore with UCS-5!" ;;
*) die "The server role '$server_role' is not supported!" ;;
esac

if ! is_ucr_true update50/skip/autoremove; then
	DEBIAN_FRONTEND=noninteractive apt-get -y --force-yes autoremove >&3 2>&3
fi

# removes temporary sources list (always required)
if [ -e "/etc/apt/sources.list.d/00_ucs_temporary_installation.list" ]; then
	rm -f /etc/apt/sources.list.d/00_ucs_temporary_installation.list
fi

# removing the atd service conf file that is setting the KillMode attribute
if [ -e "/etc/systemd/system/atd.service.d/update500.conf" ]; then
	rm -f /etc/systemd/system/atd.service.d/update500.conf
	rmdir --ignore-fail-on-non-empty /etc/systemd/system/atd.service.d/
	systemctl daemon-reload
fi

# Bug #52993: recreate initramfs for all available kernels due to removed initramfs/init
echo "recreate initramfs for all available kernels due to changes in univention-initrd..." >&3 2>&3
/usr/sbin/update-initramfs -k all -c >&3 2>&3
echo "done" >&3 2>&3

# executes custom postup script (always required)
if [ -n "${update_custom_postup:-}" ]; then
	if [ -f "$update_custom_postup" ]; then
		if [ -x "$update_custom_postup" ]; then
			echo -n "Running custom postupdate script $update_custom_postup"
			"$update_custom_postup" "$UPDATE_NEXT_VERSION" >&3 2>&3
			echo "Custom postupdate script $update_custom_postup exited with exitcode: $?" >&3
		else
			echo "Custom postupdate script $update_custom_postup is not executable" >&3
		fi
	else
		echo "Custom postupdate script $update_custom_postup not found" >&3
	fi
fi

if [ -x /usr/sbin/univention-check-templates ]; then
	if ! /usr/sbin/univention-check-templates >&3 2>&3
	then
		echo "Warning: UCR templates were not updated. Please check $UPDATER_LOG or execute univention-check-templates as root."
	fi
fi

if [ -f /var/univention-join/joined ]
then
	udm "computers/$server_role" modify \
		--binddn "${ldap_hostdn:?}" \
		--bindpwdfile "/etc/machine.secret" \
		--dn "${ldap_hostdn:?}" \
		--set operatingSystem="Univention Corporate Server" \
		--set operatingSystemVersion="$UPDATE_NEXT_VERSION" >&3 2>&3
fi

# Bug #44188: recreate and reload packetfilter rules to make sure the system is accessible
service univention-firewall restart >&3 2>&3

# Bug #51531: re-evaluate extensions startucsversion and enducsversion (always required)
listener_modules="udm_extension"
if [ "${server_role:-}" != "memberserver" ]; then
	listener_modules="$listener_modules ldap_extension"
fi
# Bug #53711: "WARNING: The "blocking locks" option is deprecated" caused by shares created in UCS4.4
if [ -e "/usr/lib/univention-directory-listener/system/samba-shares.py" ]; then
	listener_modules+=" samba-shares"
fi
echo "running univention-directory-listener-ctrl resync $listener_modules"
# shellcheck disable=SC2086
/usr/sbin/univention-directory-listener-ctrl resync $listener_modules
# Wait for listener module resync to finish
wait_period=0
while [ "$wait_period" -lt "300" ]; do
	if [ -e "/var/lib/univention-directory-listener/handlers/ldap_extension" ]; then
		ldap_ext_state=$(</var/lib/univention-directory-listener/handlers/ldap_extension)
	elif [ "${server_role:-}" = "memberserver" ]; then
		ldap_ext_state=3
	else
		ldap_ext_state=0
	fi

	if [ -e "/var/lib/univention-directory-listener/handlers/udm_extension" ]; then
		udm_ext_state=$(</var/lib/univention-directory-listener/handlers/udm_extension)
	else
		udm_ext_state=0
	fi

	if [ "$ldap_ext_state" = "3" ] && [ "$udm_ext_state" = "3" ]; then
		break
	fi
	sleep 1
	wait_period=$((wait_period+1))
done
# Wait another 30 seconds for listener postrun, as ldap_extension restarts slapd
sleep 30

# run remaining joinscripts
if [ "$server_role" = "domaincontroller_master" ]; then
	univention-run-join-scripts >&3 2>&3
fi

rm -f /etc/apt/preferences.d/99ucs500.pref /etc/apt/apt.conf.d/99ucs500

rm -f /etc/apt/sources.list.d/15_ucs-online-version.list.upgrade500-backup
rm -f /etc/apt/sources.list.d/20_ucs-online-component.list.upgrade500-backup

# Bug #47192: Remove deprecated errata components
ucr search --brief --non-empty '^repository/online/component/[1-4][.][0-9]+-[0-9]+-errata' |
  tee -a "$UPDATER_LOG" |
  cut -d: -f1 |
  xargs -r ucr unset

# Bug #52923: switch back to old fetchmail/autostart status
if [ -n "$(ucr search "^fetchmail/autostart/update500$")" ] ; then
	eval "$(ucr shell fetchmail/autostart/update500)"
	# shellcheck disable=SC2154
	if [ -z "$fetchmail_autostart_update500" ] ; then
		ucr unset fetchmail/autostart >&3 2>&3
	else
		ucr set fetchmail/autostart="$fetchmail_autostart_update500" >&3 2>&3
	fi
	ucr unset fetchmail/autostart/update500 >&3 2>&3
	echo "Please note:" >&3
	echo "The following fetchmail restart might fail if fetchmail is unconfigured." >&3
	echo "This is usually no error." >&3
	service fetchmail restart  >&3 2>&3 || :
fi

# Bug #52974: reenable libvirtd after update
for service in libvirtd virtlogd ; do
	state="$(ucr get "update/service/libvirt/${service:-}")"
	if [ -n "${state:-}" ] ; then
		if [ "${state:-}" = "masked" ] ; then
			echo "${service:-}.service was masked prior to the update - doing nothing" >&3
		else
			echo "${service:-}.service was '$state' prior to the update" >&3
			systemctl unmask "${service:-}.service" >&3 2>&3
			if [ "${state:-}" = "disabled" ] ; then
				systemctl disable "${service:-}.service" >&3 2>&3
			elif [ "${state:-}" = "enabled" ] || [ "${state:-}" = "indirect" ] ; then
				systemctl enable "${service:-}.service" >&3 2>&3
				systemctl start "${service:-}.service" >&3 2>&3
			else
				echo "WARNING: unknown state of ${service:-}.service - doing nothing" >&3
			fi
		fi
		ucr unset "update/service/libvirt/${service:-}" >&3 2>&3
	fi
done

# Bug #52971: fix __pycache__ directory permissions
find /usr/lib/python3/dist-packages/ -type d -not -perm 755 -name __pycache__ -exec chmod 755 {} \;

# Bug #55637
systemctl restart rabbitmq-server.service

# Bug #54586
# Bug #54587
if is_installed univention-s4-connector && [ -e "/etc/univention/connector/s4internal.sqlite" ]; then
	systemctl stop univention-s4-connector
	python3 - <<EOF
#!/usr/bin/python3
import sqlite3
db = sqlite3.connect('/etc/univention/connector/s4internal.sqlite')
cursor = db.cursor()
cursor.execute('select * from "S4 rejected";')
rejects = cursor.fetchall()
cursor.execute('delete from "S4 rejected"')
for key, value in rejects:
    if isinstance(value, bytes):
        value = value.decode('UTF-8')
    if isinstance(key, bytes):
        key = key.decode('UTF-8')
    cursor.execute('insert into "S4 rejected" (key, value) VALUES (?, ?)', (key, value))
db.commit()
EOF
	systemctl start univention-s4-connector
fi

if is_installed univention-ad-connector && [ -e "/etc/univention/connector/internal.sqlite" ]; then
	systemctl stop univention-ad-connector
	python3 - <<EOF
#!/usr/bin/python3
import sqlite3
db = sqlite3.connect('/etc/univention/connector/internal.sqlite')
cursor = db.cursor()
cursor.execute('select * from "AD rejected";')
rejects = cursor.fetchall()
cursor.execute('delete from "AD rejected"')
for key, value in rejects:
    if isinstance(value, bytes):
        value = value.decode('UTF-8')
    if isinstance(key, bytes):
        key = key.decode('UTF-8')
    cursor.execute('insert into "AD rejected" (key, value) VALUES (?, ?)', (key, value))
db.commit()
EOF
	systemctl start univention-ad-connector
fi

echo "


****************************************************
*    THE UPDATE HAS BEEN FINISHED SUCCESSFULLY.    *
* Please make a page reload of UMC and login again *
****************************************************


" >&3 2>&3

echo "done."
date >&3

# make sure that UMC server is restarted (Bug #43520, Bug #33426)
at now >&3 2>&3 <<EOF
sleep 30
exec 3>>"$UPDATER_LOG"
# Bug #47436: Only re-enable apache2 and umc if system-setup 
# is not running. System-setup will re-enable apache2 and umc.
if ! pgrep -l -f /usr/lib/univention-system-setup/scripts/setup-join.sh; then
  /usr/share/univention-updater/enable-apache2-umc --no-restart >&3 2>&3
fi
service univention-management-console-server restart >&3 2>&3
service univention-management-console-web-server restart >&3 2>&3
# the file path moved. during update via UMC the apache is not restarted. The new init script therefore checks the wrong pidfile which fails restarting.
cp /var/run/apache2.pid /var/run/apache2/apache2.pid
service apache2 restart >&3 2>&3
# Bug #48808
univention-app update >&3 2>&3 || true
univention-app register --app >&3 2>&3 || true
if dpkg -l univention-samba4 | grep -q ^ii; then
	if samba-tool drs showrepl  2>&1 | egrep -q "DsReplicaGetInfo (.*) failed"; then
		/etc/init.d/samba restart
	fi
	sleep 5
	if [ "$(pgrep -c '(samba|rpc[([]|s3fs|cldap|ldap|drepl|kdc|kcc|ntp_signd|dnsupdate|winbindd|wrepl)') -lt 10 ]; then  # should be about 25
		echo "WARNING "
		echo "WARNING: There are too few samba processes running. Please check functionality before updating other UCS systems!"
		echo "WARNING "
	fi
	if ! univention-s4search -s base -b '' defaultNamingContext >/dev/null 2>&1; then
		echo "ERROR "
		echo "ERROR: Samba/AD LDAP is not available. Please check functionality before updating other UCS systems!"
		echo "ERROR "
	elif
fi
EOF

exit 0
