# vim:set ft=sh:
#
# Common library function for updater test
# 1. All modifications done though "ucr" are automatically undone on exit
# 2. Extra files for apache should be symlinked from ${BASEDIR}, which are removed on exit
#
eval "$(univention-config-registry shell | sed -e 's/^/declare -r _/')"
# shellcheck disable=SC2154,SC2034
declare -i major="${_version_version%.*}"
declare -i minor="${_version_version#*.}"
pkgname="test-$$-${RANDOM}"
# shellcheck disable=SC2034
repoprefix="univention-repository"
ARCH=$(dpkg-architecture -qDEB_HOST_ARCH 2>/dev/null)

bug43914 () {
	local name="$1"
	[[ "$name" = [78]* ]] || return 0

	local DST="$HOME/artifacts"
	mkdir -p "$DST"
	UT_VERBOSE="$DST/ucs-test-$name"

	local IFS=.
	# shellcheck disable=SC2046
	set -- $(uname -r)  # IFS
	case "$1" in
	3) apt-get install -qq "linux-tools-$1.$2" </dev/null || return $? ;;
	4) apt-get install -qq "linux-perf-$1.$2" </dev/null || return $? ;;
	esac
	sysctl kernel.perf_event_paranoid=-1 || :
	mountpoint -q /sys/kernel/debug || mount -o remount,mode=755 /sys/kernel/debug || :

	[ -n "${UT_PERF:-}" ] && return 0
	exec env UT_PERF=$$ perf record -o "$DST/ucs-test-$name.perf" -g -F 10 -q -- "$SHELL" "$0" "$@" || :
}
#bug43914 "${0##*/}"
# if UT_VERBOSE is set, output messages to STDERR, otherwise /dev/null
case "${UT_VERBOSE-}" in
	/?*|./?*)
		exec 3>&2 4>"${UT_VERBOSE}.$$"
		PS4='+${BASH_SOURCE}:${LINENO}:${FUNCNAME[0]}@${SECONDS}: '
		BASH_XTRACEFD=4
		set -x
		;;
	"") exec 3>/dev/null ;;
	?*) exec 3>&2 ;;
esac

unset TMPDIR # Unset user-defines base-directroy for mktemp
BASEDIR="$(mktemp -d -p /var/lib/ucs-test)"
echo "BASEDIR=\"${BASEDIR}\"" >&3
# Need to be accessible by apache2, otherwise 403 FORBIDDEN
chmod 755 "${BASEDIR}"
# Make a backup
cp /etc/univention/base*.conf "${BASEDIR}/"
cp /etc/apt/trusted.gpg "${BASEDIR}/trusted.gpg"

# Wrap univention-config-registry to later undo any changes
declare -a _reset=(version/version version/patchlevel version/erratalevel)
ucr () { # (get|set|unset) name[=value]...
	local mode="${1}"
	case "${mode}" in
		set|unset)
			shift
			local name_value
			for name_value in "$@"
			do
				_reset+=("${name_value%%[?=]*}")
			done
			univention-config-registry "${mode}" "$@" >&3 2>&3
			;;
		*)
			univention-config-registry "$@"
			;;
	esac
}

cleanup () { # Undo all changes
	local rv="$?"
	set +e
	trap - EXIT

	kill_proxy

	[ -f "${BASEDIR}/reenable_mirror" ] && a2ensite univention-repository >&3 2>&3
	find -P /etc/apache2 -lname "${BASEDIR}/*" -exec rm -f {} +
	apache2ctl restart >&3 2>&3
	sleep 3

	declare -a reset remove
	local name sname
	for name in "${_reset[@]}"
	do
		local sname="_${name//\//_}"
		if [ -n "${!sname}" ]
		then
			reset+=("${name}"="${!sname}")
		else
			remove+=("${name}")
		fi
	done
	# shellcheck disable=SC2128
	[ -n "${remove}" ] && univention-config-registry unset "${remove[@]}" >&3 2>&3
	# shellcheck disable=SC2128
	[ -n "${reset}" ] && univention-config-registry set "${reset[@]}" >&3 2>&3
	cp "${BASEDIR}"/base*.conf /etc/univention/
	cp "${BASEDIR}/trusted.gpg" /etc/apt/trusted.gpg
	rm -f /etc/apt/sources.list.d/00_ucs_update_in_progress.list
    rm -f /etc/apt/sources.list.d/00_ucs_temporary_installation.list


	[ -x /etc/init.d/cron ] && [ -f "${BASEDIR}/reenable_cron" ] && invoke-rc.d cron start >&3 2>&3 3>&-

	# rm -rf "${BASEDIR}"
	echo "=== RESULT: ${RETVAL} ==="
	echo "${BASEDIR}"
	return "$rv"
}
trap cleanup EXIT
failure () { # Report failed command
	set +e +x
	trap - ERR
	[ ${BASH_SUBSHELL} -eq 0 ] && return 0 # do not exit the controlling shell

	echo "**************** Test failed above this line ****************" >&2
	echo "ERROR ${0}:${BASH_LINENO[*]}" >&2
	echo "ERROR ${BASH_COMMAND}" >&2
	[ -s "${BASEDIR}/apache2.log" ] && cat "${BASEDIR}/apache2.log"
	cat /etc/apt/sources.list /etc/apt/sources.list.d/*.list || :
	sleep "${UT_DELAY:-0}"
	exit "${RETVAL:-140}" # internal error
}
trap 'failure ${LINENO}' ERR
set -E # functions inherit ERR

setup_apache () { # Setup apache for repository [--port ${port}] [${prefix}]
	local hostname=localhost
	if [ "${1}" = "--port" ]
	then
		local port="${2}"
		local listen="Listen ${port}"
		shift 2
	fi
	REPOPREFIX="${1}"
	REPODIR="${BASEDIR}${REPOPREFIX:+/${REPOPREFIX#/}}"
	[ -n "${REPOPREFIX}" ] && local alias="Alias /${REPOPREFIX} ${REPODIR}"
	cat <<-EOF >"${BASEDIR}/apache2.conf"
	${listen}
	<VirtualHost ${hostname}${port:+:${port}}>
	DocumentRoot ${BASEDIR}
	CustomLog ${BASEDIR}/apache2.log combined
	${alias}
	<Directory ${REPODIR}>
			   AllowOverride All
			   Options +Indexes
			   Require all granted
	</Directory>
	</VirtualHost>
	EOF
	ln -s "${BASEDIR}/apache2.conf" /etc/apache2/sites-enabled/univention-repository.$$.conf
	mkdir -p "${REPODIR}"
	if test -f /etc/apache2/sites-enabled/univention-repository.conf
	then
		touch "${BASEDIR}/reenable_mirror"
		a2dissite univention-repository >&3 2>&3
	fi
	truncate -s 0 "${BASEDIR}/apache2.log"
	apache2ctl restart >&3 2>&3
}

config_proxy () { # Run HTTP proxy: ...
	kill_proxy
	eval "$(python3 proxy.py -f -p 0 "$@" 3>&-)"
}
kill_proxy () { # Kill HTTP proxy
	[ -n "${proxy_pid:-}" ] || return 0
	kill "${proxy_pid:?}" 2>&3
	unset proxy_pid
}

config_repo () { # Configure use of repository from local apache
	local server=localhost
	local port=80
	local prefix="${REPOPREFIX}"
	declare -a extra
	while [ $# -ge 1 ]
	do
		case "${1}" in
			/*) prefix="${1#/}" ;;
			:[1-9]*) port="${1#:}" ;;
			?*=*) extra+=("${1}") ;;
			*:[1-9]*) server="${1%:*}" ; port="${1##*:}" ;;
			*) server="${1}" ;;
		esac
		shift
	done
	if [ -x /etc/init.d/cron ] && pidof cron >/dev/null
	then
		touch "${BASEDIR}/reenable_cron"
		invoke-rc.d cron stop
	fi
	ucr set \
		update/available= \
		local/repository=no \
		repository/mirror=no \
		repository/online=yes \
		repository/online/server="${server}" \
		repository/online/port="${port}" \
		repository/online/prefix="${prefix}" \
		"${extra[@]}" >&3 2>&3
}

config_mirror () { # Configure mirror to use repository from local apache
	local server=localhost
	local port=80
	local prefix="${REPOPREFIX}"
	local mirror="${BASEDIR}/mirror"
	declare -a extra
	while [ $# -ge 1 ]
	do
		case "${1}" in
			/*) prefix="${1#/}" ;;
			:[1-9]*) port="${1#:}" ;;
			?*=*) extra+=("${1}") ;;
			*:[1-9]*) server="${1%:*}" ; port="${1##*:}" ;;
			*) server="${1}" ;;
		esac
		shift
	done
	mkdir -p "${mirror}"
	if [ -x /etc/init.d/cron ] && pidof cron >/dev/null
	then
		touch "${BASEDIR}/reenable_cron"
		invoke-rc.d cron stop
	fi
	ucr set \
		local/repository=yes \
		repository/online=no \
		repository/mirror=yes \
		repository/mirror/basepath="${mirror}" \
		repository/mirror/server="${server}" \
		repository/mirror/port="${port}" \
		repository/mirror/prefix="${prefix}" \
		"${extra[@]}" >&3 2>&3
}

allpatchlevels () { # All ${major}.${minor}-0 ... ${major}.${minor}-${patchlevel}
	# shellcheck disable=SC2086
	set -- ${1//[.-]/ }  # IFS
	declare -i patchlevel
	for ((patchlevel=0; patchlevel<=${3}; patchlevel+=1))
	do
		echo "${1}.${2}-${patchlevel}"
	done
}

allminors () { # All ${major}.0-0 ... ${major}.${minor}-0 ... ${major}.${minor}-${patchlevel}
	# shellcheck disable=SC2086
	set -- ${1//[.-]/ }  # IFS
	declare -i minor
	for ((minor=0; minor<=${2}; minor+=1))
	do
		echo "${1}.${minor}-0"
	done
	allpatchlevels "${1}.${2}-${3}"
}

have () { command -v "$1" >/dev/null 2>&1; }

declare -a DIRS
mkpdir () { # Create pool directory ${dir}
	declare -a versions parts archs
	while [ $# -ge 1 ]
	do
		case "${1}" in
			[1-9]*.[0-9]*-[0-9]*) versions+=("${1}") ;;
			[1-9]*.[0-9]*--errata[0-9]*) versions+=("${1}") ;;
			[1-9]*.[0-9]*--component/*) versions+=("${1}") ;;
			maintained|unmaintained) parts+=("${1}") ;;
			all|i386|amd64) archs+=("${1}") ;;
			extern|*--sec*) echo "Deprecated ${1}" >&2 ; return 2 ;;
			*) echo "Unknown ${1}" >&2 ; return 2 ;;
		esac
		shift
	done
	local version part arch
	for version in "${versions[@]}"
	do
		for part in "${parts[@]}"
		do
			for arch in "${archs[@]}"
			do
				DIR="${REPODIR}/${version%%-*}/${part}/${version#*--}/${arch}"
				DIRS+=("${DIR}")
				mkdir -p "${DIR}"
				touch "${DIR}/Packages"
			done
		done
	done
	return 0
}

mkdeb () { # Create dummy package [name [version [arch [dir [postinst]]]]]
	local name="${1:-test}"
	local version="${2:-1}"
	local arch="${3:-all}"
	local dir="${4:-${DIR}}"
	mkdir -p "${BASEDIR}/${name}-${version}/DEBIAN"
	cat <<-EOF >"${BASEDIR}/${name}-${version}/DEBIAN/control"
	Package: ${name}
	Version: ${version}
	Architecture: ${arch}
	Maintainer: UCS Test <test@univention.de>
	Installed-Size: 1
	Section: unknown
	Priority: optional
	Description: test $0
	EOF
	cat <<-EOF >"${BASEDIR}/${name}-${version}/DEBIAN/postinst"
	#!/bin/sh
	echo "${name}-${version}" >>"${BASEDIR}/install.log"
	echo "${name}-${version}.postinst \$(grep -Er "^(status|phase)=" /var/lib/univention-updater/univention-updater.status | sort | tr "\n" " ")" >>"${BASEDIR}/install-status.log"
	${5}
	EOF
	chmod 755 "${BASEDIR}/${name}-${version}/DEBIAN/postinst"
	DEB="${BASEDIR}/${name}_${version}_${arch}.deb"
	dpkg-deb -b "${BASEDIR}/${name}-${version}" "${DEB}" >&3 2>&3
	[ -z "${dir}" ] || cp "${DEB}" "${dir}/"
}

mkdsc () { # Create dummy source package [name [version [arch [dir]]]]
	local name="${1:-test}"
	local version="${2:-1}"
	local arch="${3:-all}"
	local dir="${4:-${DIR}}"
	mkdir -p "${BASEDIR}/${name}-${version}/debian"
	cat <<-EOF >"${BASEDIR}/${name}-${version}/debian/changelog"
	${pkgname} (${version}) unstable; urgency=low

	  * ucs-test $0

	 -- Univention GmbH <packages@univention.de>  $(date -R)
	EOF
	cat <<-EOF >"${BASEDIR}/${name}-${version}/debian/control"
	Source: ${pkgname}
	Maintainer: Univention GmbH <packages@univention.de>
	Standards-Version: 3.6.1

	Package: ${pkgname}
	Architecture: ${ARCH}
	EOF
	cat <<-EOF >"${BASEDIR}/${name}-${version}/debian/rules"
	#!/usr/bin/make -f
	clean build binary-indep binary-arch binary: true
	EOF
	: >"${BASEDIR}/${name}-${version}/debian/copyright"
	(cd "${BASEDIR}" && dpkg-source -b "${pkgname}-${version}") >&3 2>&3
	TGZ="${BASEDIR}/${name}_${version}.tar.gz"
	DSC="${BASEDIR}/${name}_${version}.dsc"
	if mkgpg
	then
		gpgsign "${DSC}"
	fi
	[ -z "${dir}" ] || mv "${DSC}" "${TGZ}" "${dir}/"
}

mkpkg () { # Create Package files for ${1}. Optional arguments go to dpkg-scanpackages.
	local dir="${1:-${DIR}}"
	shift
	cd "${dir}/../.." || return $?
	local subdir="${dir#${PWD}/}"
	dpkg-scanpackages "${@}" "${subdir}" > "${dir}/Packages" 2>&3
	gzip -n -9 <"${dir}/Packages" >"${dir}/Packages.gz"
	bzip2 -9 <"${dir}/Packages" >"${dir}/Packages.bz2"
	cd "${OLDPWD}" || return $?

	mkgpg
	cd "${dir}" || return $?
	rm -f Release Release.tmp Release.gpg
	apt-ftparchive \
		-o "APT::FTPArchive::Release::Origin=Univention" \
		-o "APT::FTPArchive::Release::Label=Univention" \
		-o "APT::FTPArchive::Release::Version=${subdir%%/*}" \
		-o "APT::FTPArchive::Release::Codename=${subdir}" \
		release . >Release.tmp 2>&3
	mv Release.tmp Release

	gpgsign Release
	cd "${OLDPWD}" || return $?
}

gpgsign () { # sign file
	mkgpg
	local out sign
	case "${1:-}" in
	Release|*.sh)
		sign=--detach-sign
		out="${1}.gpg"
		cp "$1" "${GPG_DIR}/in"
		;;
	""|-)
		sign=--detach-sign
		out="$2"
		cat "$1" >"${GPG_DIR}/in"
		;;
	*.dsc)
		sign=--clearsign
		out="${1}"
		(cat "$1" && echo "") >"${GPG_DIR}/in"
		;;
	*)
		echo "Failed to sign '${1}'" >&2
		return 1
		;;
	esac
	rm -f "${GPG_DIR}/out"
	chroot "${GPG_DIR}" "${GPG_BIN}" \
		--batch \
		--pinentry-mode=loopback \
		--passphrase '' \
		--armor \
		--default-key "${GPGID}" \
		"${sign}" \
		--output out in
	cp "${GPG_DIR}/out" "${out}"
}

mksrc () { # Create Sources files for ${1}. Optional arguments go to dpkg-scansources.
	local dir="${1:-${DIR}}"
	shift
	cd "${dir}/../.." || return $?
	local subdir="${dir#${PWD}/}"
	dpkg-scansources "${@}" "${subdir}" > "${dir}/Sources" 2>&3
	gzip -n -9 <"${dir}/Sources" >"${dir}/Sources.gz"
	bzip2 -9 <"${dir}/Sources" >"${dir}/Sources.bz2"
	cd "${OLDPWD}" || return $?

	mkgpg
	cd "${dir}" || return $?
	rm -f Release Release.tmp Release.gpg
	apt-ftparchive \
		-o "APT::FTPArchive::Release::Origin=Univention" \
		-o "APT::FTPArchive::Release::Label=Univention" \
		-o "APT::FTPArchive::Release::Version=${subdir%%/*}" \
		-o "APT::FTPArchive::Release::Codename=${subdir}" \
		release . >Release.tmp 2>&3
	mv Release.tmp Release

	gpgsign Release
	cd "${OLDPWD}" || return $?
}

mkgpg () { # Create GPG-key for secure APT
	GPG_BIN=/usr/bin/gpg
	GPG_DIR="${BASEDIR}/gpg.chroot"
	install -m 0700 -d "${GPG_DIR}${HOME}/.gnupg"
	echo 'allow-loopback-pinentry' >"${GPG_DIR}${HOME}/.gnupg/gpg-agent.conf"
	# Non-blocking GnuPG using /dev/_u_random
	(
		echo "${GPG_BIN}"
		ldd "${GPG_BIN}" | grep --only '/\S\+'
		echo "${GPG_BIN}-agent"
		ldd "${GPG_BIN}-agent" | grep --only '/\S\+'
		echo /dev/urandom
		echo /dev/null
	) | sort -u | cpio --pass-through --make-directories --dereference "${GPG_DIR}"
	ln -s urandom "${GPG_DIR}/dev/random"
	GPGSTATUS="${GPG_DIR}/test.status"
	chroot "${GPG_DIR}" "${GPG_BIN}" \
		--batch \
		--yes \
		--pinentry-mode=loopback \
		--passphrase '' \
		--status-fd 3 \
		--quick-generate-key 'ucs-test@univention.de' dsa default 1d 3>"${GPGSTATUS}"
	GPGID=$(sed -ne 's/^\[GNUPG:\] KEY_CREATED P //p' "${GPGSTATUS}")
	GPGPUB="${GPG_DIR}/test.pub"
	chroot "${GPG_DIR}" "${GPG_BIN}" --armor --export "$GPGID" >"$GPGPUB"
	apt-key add "${GPGPUB}"
	mkgpg () { true; }
	return 0
}

mksh () { # Create shell scripts $@ in $1
	local dir="${1}" ret='$?'
	shift
	while [ $# -ge 1 ]
	do
		case "${1}" in
		--return) ret="${2}" ; shift 2 ;;
		esac
		cat <<-EOF >"${dir}/${1}.sh"
		#!/bin/sh
		echo "${dir}/${1}.sh ${RANDOM}" "\$@" >>"${BASEDIR}/install.log"
		echo "${1}.sh "\$@" \$(grep -Er "^(status|phase)=" /var/lib/univention-updater/univention-updater.status | sort | tr "\n" " ")" >>"${BASEDIR}/install-status.log"
		exit ${ret}
		EOF
		chmod 755 "${dir}/${1}.sh"
		case "${_repository_online_verify:-}" in
			0|false|no|off) return 0 ;;
		esac
		if mkgpg
		then
			gpgsign "${dir}/${1}.sh"
		fi
		shift
	done
}

split_repo_path () { # Split repository path into atoms
	local oldifs="${IFS}"
	local IFS=/
	# shellcheck disable=SC2086
	set -- ${1#${REPODIR}/}  # IFS
	IFS="${oldifs}"
	local version part arch
	version="${1}"
	part="${2}"
	case "${3}" in
		"${version}-"[0-9]*) version="${3}" ;;
		errata*) version="${version}--${3}" ;;
		component) version="${version}--component/${4}" ; shift ;;
		*) echo "Unknown ${3}" >&2 ; return 2 ;;
	esac
	arch="${4}"
	echo "${version}" "${part}" "${arch}"
}

checkapt () { # Check for apt-source statement ${1}
	local files='/etc/apt/sources.list.d/*.list'
	local prefix=deb
	local pattern
	while [ $# -ge 1 ]
	do
		case "${1}" in
			--mirror) files=/etc/apt/mirror.list && shift ; continue ;;
			--source|source) prefix=deb-src && shift ; continue ;;
			http*) pattern="^${prefix} ${1}" ;;
			[1-9]*.[0-9]*-[0-9]*) pattern="^${prefix} .*/${1%-*}/.* ${1}/.*/$" ;;
			[1-9]*.[0-9]*--errata[0-9]*) pattern="^${prefix} .*/${1%%-*}/.* ${1#*--}/.*/" ;;
			[1-9]*.[0-9]*--component/*) pattern="^${prefix} .*/${1%%-*}/.*/component/\? ${1#*--component/}/.*/" ;;
			maintained|unmaintained) pattern="^${prefix} .*/${1}/\(component/\?\)\? .*/.*/" ;;
			all|${ARCH}|extern) pattern="^${prefix} .*/\(component/\?\)\? .*/${1}/" ;;
			i386|amd64) shift ; continue ;;
			/*) # shellcheck disable=SC2046
				set -- "$@" $(split_repo_path "${1}") && shift  # IFS
				continue
				;;
			*) echo "Unknown ${1}" >&2 ; return 2 ;;
		esac
		if ! grep -q "${pattern}" ${files}
		then
			echo "Failed '${pattern}'" >&2
			grep -v '^#\|^[[:space:]]*$' ${files} >&2
			return 1
		fi
		shift
	done
}

checkdeb () { # Check is package was installed in versions $@
	local pkgname="${1}"
	while [ $# -gt 1 ]
	do
		shift
		if ! grep -Fqx "${pkgname}-${1}" "${BASEDIR}/install.log"
		then
			echo "Failed ${pkgname}-${1}" >&2
			cat "${BASEDIR}/install.log" >&2
			return 1
		fi
	done
}

checkmirror () { # Check mirror for completeness: required-dirs... -- forbidden-dirs...
	local srcdir="${REPODIR}"
	local dstdir="${BASEDIR}/mirror"
	local skeldir="${dstdir}/skel/${REPOPREFIX}"
	local port=80

	# Symlink
	test "$(readlink "${dstdir}/mirror/univention-repository")" = .

	# Directories
	local invert
	while [ $# -ge 1 ]
	do
		if [ "${1}" = -- ]
		then
			invert=!
		else
			test ${invert} -d "${dstdir}/mirror/${1#${srcdir}/}" || return 1
		fi
		shift
	done

	# Mirrored files
	local cmd uri dist
	while read -r cmd uri dist
	do
		[ "${cmd}" = deb ] || continue
		[[ "${uri}" =~ 'http://localhost'(":${port}")?"/${REPOPREFIX}/"(.*) ]] || continue
		local prefix="${BASH_REMATCH[2]}"
		cmp "${srcdir}/${prefix}/${dist}/Packages" "${skeldir}/${prefix}/${dist}/Packages"
		cmp "${srcdir}/${prefix}/${dist}/Packages.gz" "${skeldir}/${prefix}/${dist}/Packages.gz"
		test -s "${dstdir}/mirror/${prefix}/${dist}/Packages" || return 1
		test -s "${dstdir}/mirror/${prefix}/${dist}/Packages.gz" || return 1

		local oldifs="${IFS}"
		local IFS=$'\n'
		# shellcheck disable=SC2046
		set -- $(cd "${srcdir}" && find "${prefix}/${dist}" -name \*.deb -o -name \*.sh)  # IFS
		IFS="${oldifs}"
		while [ $# -ge 1 ]
		do
			cmp "${srcdir}/${1}" "${dstdir}/mirror/${1}" || return 1
			shift
		done
	done </etc/apt/mirror.list
}



#### UCS 5 specific
declare -a COMPRESS=('xz=.xz' 'gzip=.gz')  # 'bzip2=.bz2'
# BUG: univention.updater.tools.UCSRepoPool et al. still has hard-coded `.gz`!

wait_for_updater_lock () {
	# wait up to 60 seconds
	declare -i i
	for ((i=0; i<60; i++))
	do
		[ -f /var/lock/univention-updater ] ||
			return 0
		sleep 1
	done
	echo "ERROR: wait_for_updater_lock ran into a timeout!"
	ps axfwww
	grep -Hr . /var/lock/univention-updater || :
}

declare -a DIRS
mkpdir_ucs5 () { # Create package directory ${dir}
	declare -a versions component_versions parts archs
	local dir suite='ucs'
	while [ $# -ge 1 ]
	do
		case "${1}" in
			[1-9]*.[0-9]*-[0-9]*)
				versions+=("${1%--*}")
				;;
			[1-9]*.[0-9]*--errata[0-9]*)
				versions+=("${1%--*}")
				suite='errata'
				;;
			[1-9]*.[0-9]*--component/*)
				versions+=("${1%--*}-0")
				component_versions+=("${1}")
			;;
			maintained|unmaintained) parts+=("${1}") ;;
			all|i386|amd64) archs+=("${1}") ;;
			extern|*--sec*) echo "Deprecated ${1}" >&2 ; return 2 ;;
			*) echo "Unknown ${1}" >&2 ; return 2 ;;
		esac
		shift
	done

	DIR_POOL="${REPODIR}/pool/main"
	mkdir -p "${DIR_POOL}"

	local version arch release_type version_stripped
	for version in "${versions[@]}"
	do
		echo "Creating for $version"
		for release_type in 'ucs' 'errata'
		do
			version_stripped="${version%--*}"
			version_stripped="${version_stripped//[^0-9]/}"
			for arch in "${archs[@]}"
			do
				# `all` packages are listed within the `binary-$ARCH` section unless
				# 'Release.Architectures' explicitly includes 'all'
				[ "$arch" = 'all' ] &&
					continue
				dir="${REPODIR}/dists/${release_type}${version_stripped}/main/binary-${arch}/"
				[ "$release_type" = "$suite" ] &&
					DIR="${dir}"
				# shellcheck disable=SC2076
				if [[ ! " ${DIRS[*]} " =~ " $dir " ]]
				then
					DIRS+=("${dir}")
					mkdir -p "${dir}"
					mkpkg "${dir}" "${DIR_POOL}"
				fi
			done
		done
	done
	for version in "${component_versions[@]}"
	do
		echo "Creating for $version"
		for part in "${parts[@]}"
		do
			for arch in "${archs[@]}"
			do
				DIR="${REPODIR}/${version%%-*}/${part}/${version#*--}/${arch}"
				DIRS+=("${DIR}")
				mkdir -p "${DIR}"
				touch "${DIR}/Packages"
				compress "${DIR}/Packages"
			done
		done
	done
}

dirs_except () {  # Array substract: elements... -- remove...
	result=("${DIRS[@]}")
	local i
	while [ $# -ge 1 ]
	do
		for i in "${!result[@]}"
		do
			[ "$1" = "${result[i]}" ] && unset result["$i"]
		done
		shift
	done
}

mkdeb_ucs5 () { # Create dummy package: [name [version [arch [dir [postinst]]]]]
	local name="${1:-test}"
	local version="${2:-1}"
	local arch="${3:-all}"
	local dir="${4:-${DIR_POOL}}"
	mkdir -p "${BASEDIR}/${name}-${version}/DEBIAN"
	cat <<-EOF >"${BASEDIR}/${name}-${version}/DEBIAN/control"
	Package: ${name}
	Version: ${version}
	Architecture: ${arch}
	Maintainer: UCS Test <test@univention.de>
	Installed-Size: 1
	Section: unknown
	Priority: optional
	Description: test $0
	EOF
	cat <<-EOF >"${BASEDIR}/${name}-${version}/DEBIAN/postinst"
	#!/bin/sh
	echo "${name}-${version}" >>"${BASEDIR}/install.log"
	echo "${name}-${version}.postinst \$(grep -Er "^(status|phase)=" /var/lib/univention-updater/univention-updater.status | sort | tr "\\n" ' ')" >>"${BASEDIR}/install-status.log"
	${5}
	EOF
	chmod 755 "${BASEDIR}/${name}-${version}/DEBIAN/postinst"
	DEB="${BASEDIR}/${name}_${version}_${arch}.deb"
	dpkg-deb -b "${BASEDIR}/${name}-${version}" "${DEB}" >&3 2>&3 || return $?

	case "$dir" in
	'') ;;
	*/pool/*) install -m 644 -t "${dir}/${name:0:1}/" -D "${DEB}" ;;
	*) install -m 644 -t "${dir}/" -D "${DEB}" ;;
	esac
}

mkdsc_ucs5 () { # Create dummy source package: [name [version [arch [dir]]]]
	local name="${1:-test}"
	local version="${2:-1}"
	local arch="${3:-all}"
	local dir="${4:-${DIR}}"
	mkdir -p "${BASEDIR}/${name}-${version}/debian"
	cat <<-EOF >"${BASEDIR}/${name}-${version}/debian/changelog"
	${pkgname} (${version}) unstable; urgency=low

	  * ucs-test $0

	 -- Univention GmbH <packages@univention.de>  $(date -R)
	EOF
	cat <<-EOF >"${BASEDIR}/${name}-${version}/debian/control"
	Source: ${pkgname}
	Maintainer: Univention GmbH <packages@univention.de>
	Standards-Version: 3.6.1

	Package: ${pkgname}
	Architecture: ${ARCH}
	EOF
	cat <<-EOF >"${BASEDIR}/${name}-${version}/debian/rules"
	#!/usr/bin/make -f
	clean build binary-indep binary-arch binary: true
	EOF
	: >"${BASEDIR}/${name}-${version}/debian/copyright"
	(cd "${BASEDIR}" && dpkg-source -b "${pkgname}-${version}") >&3 2>&3
	TGZ="${BASEDIR}/${name}_${version}.tar.gz"
	DSC="${BASEDIR}/${name}_${version}.dsc"
	if mkgpg
	then
		gpgsign "${DSC}"
	fi

	case "$dir" in
	'') ;;
	*/pool/*) install -m 644 -t "${dir}/${name:0:1}/" -D "${DSC}" "${TGZ}" ;;
	*) install -m 644 -t "${dir}/" -D "${DSC}" "${TGZ}" ;;
	esac
}

mkpkg_ucs5 () { # Create Package files in ${1} for packages in ${2}. Optional arguments go to dpkg-scanpackages.
	local dir="${1:-${DIR}}"
	shift
	local dir_pool="${1:-${DIR_POOL}}"
	shift
	local rel_pool_dir="${dir_pool#${REPODIR}/}"
	rel_pool_dir="${rel_pool_dir#*/component/}"
	cd "${dir_pool%${rel_pool_dir}}" || return $?
	dpkg-scanpackages "${@}" "${rel_pool_dir}" > "${dir}/Packages" 2>&3 # || return $?
	compress "${dir}/Packages"
	cd "${OLDPWD}" || return $?

	mkgpg
	cd "${dir%/main/binary-*}" || return $?
	rm -f Release Release.tmp Release.gpg
	local codename=${dir#${REPODIR}/}
	codename="${codename#dists/}"
	codename="${codename%/main/binary-*}"
	apt-ftparchive \
		-o "APT::FTPArchive::Release::Architectures=${ARCH}" \
		-o "APT::FTPArchive::Release::Origin=Univention" \
		-o "APT::FTPArchive::Release::Label=Univention Corporate Server" \
		-o "APT::FTPArchive::Release::Version=${REPODIR%%/*}" \
		-o "APT::FTPArchive::Release::Codename=${codename}" \
		release . >Release.tmp 2>&3
	mv Release.tmp Release

	gpgsign InRelease
	gpgsign Release
	cd "${OLDPWD}" || return $?

	for destname in "main" "non-free" "contrib"
	do
		local targetdir="${dir%/main/binary-*}/$destname/binary-${ARCH}"
		[ ! -e "$targetdir" ] && continue
		cd "$targetdir" || return $?
		codename="$destname/binary-${ARCH}"
		apt-ftparchive \
			-o "APT::FTPArchive::Release::Architectures=${ARCH}" \
			-o "APT::FTPArchive::Release::Origin=Univention" \
			-o "APT::FTPArchive::Release::Label=Univention Corporate Server" \
			-o "APT::FTPArchive::Release::Version=${REPODIR%%/*}" \
			-o "APT::FTPArchive::Release::Codename=${codename}" \
			-o "APT::FTPArchive::Release::Components=main non-free contrib" \
			release . >Release.tmp 2>&3
		mv Release.tmp Release
		gpgsign Release
		cd "${OLDPWD}" || return $?
	done

	python ./create_releases_json.py "$REPODIR"
}

compress () { # compress file: <Packages|Sources>
	local comp
	for comp in "${COMPRESS[@]}"
	do
		"${comp%=*}" --keep --force "$1"
	done
}


checkapt_ucs5 () { # Check for apt.source statement ${1}: [--mirror] [[--]source] [/path] [http*] [(ucs|errata)XXX] [[un]maintained] [X.Y-(Z|--errataZ|--component/Z]
	local files='/etc/apt/sources.list.d/*.list'
	local prefix=deb
	local pattern
	while [ $# -ge 1 ]
	do
		case "${1}" in
			--mirror) files=/etc/apt/mirror.list && shift ; continue ;;
			--source|source) prefix=deb-src && shift ; continue ;;
			http*) pattern="^${prefix} ${1}" ;;
			ucs[1-9][0-9][0-9]) pattern="^${prefix} .* $1 main$" ;;
			errata[1-9][0-9][0-9]) pattern="^${prefix} .* $1 main$" ;;
			[1-9]*.[0-9]*.[0-9]*-[0-9]*) pattern="^${prefix} .*/${1%-*}/.* ${1}/.*/$" ;;
			[1-9]*.[0-9]*.[0-9]*--errata[0-9]*) pattern="^${prefix} .*/${1%%-*}/.* ${1#*--}/.*/" ;;
			[1-9]*.[0-9]*.[0-9]*--component/*) pattern="^${prefix} .*/${1%%-*}/.*/component/\\? ${1#*--component/}/.*/" ;;
			maintained|unmaintained) pattern="^${prefix} .*/${1}/\\(component/\\?\\)\\? .*/.*/" ;;
			all|${ARCH}|extern) pattern="^${prefix} .*/\\(component/\\?\\)\\? .*/${1}/" ;;
			i386|amd64) shift ; continue ;;
			binary-i386|binary-amd64) shift ; continue ;;
			main) shift ; continue ;;
			/*) # shellcheck disable=SC2046
				set -- "$@" $(python ./split_repo_path.py "${REPODIR}" "${1}") && shift  # IFS
				continue
				;;
			*) echo "Unknown ${1}" >&2 ; cat $files; return 2 ;;
		esac
		if ! grep -q "${pattern}" ${files}
		then
			echo "Failed '${pattern}'" >&2
			grep -v '^#\|^[[:space:]]*$' ${files} >&2
			grep 'error' ${files} >&2
			return 1
		fi
		shift
	done
}

