#!/bin/bash
#
# Execute UCS tests in EC2 or KVM environment
#

# defaults for release
release='5.2-0'
old_release='5.0-6'
kvm_template_version='5.2-0+e0'
# AMI: Univention Corporate Server (UCS) 5.0 (official image) rev. 7
current_ami=ami-09fefd41ed2cea5a4
# AMI: Univention Corporate Server (UCS) 5.0 (official image) rev. 7
old_ami=ami-09fefd41ed2cea5a4

# defaults
kvm_template='generic-unsafe'
kvm_operating_system='UCS'
kvm_build_server='tross.knut.univention.de'
kvm_memory='4096M'
kvm_cpus='1'
kvm_label_suffix=''
exact_match='false'
ucsschool_release='scope'
shutdown='false'
openstack_image_name='UCS 5.2-0'
source_iso="/var/univention/buildsystem2/isotests/ucs_${release}-latest-amd64.iso"

# some internal stuff
image="${DIMAGE:-gitregistry.knut.univention.de/univention/dist/ucs-ec2-tools}"
debug="${DEBUG:=false}"
docker="${DOCKER:=true}"
docker_env_file="$(mktemp)"

have () {
	command -v "$1" >/dev/null 2>&1
}

RED='' GREEN='' BLUE='' NORM=''
if [ -n "${TERM:-}" ] && [ -t 1 ] && have tput
then
	term () {
		tput "$@"
	}
	RED="$(term setaf 1)"
	GREEN="$(term setaf 2)"
	BLUE="$(term setaf 4)"
	BOLD="$(term bold)"
	NORM="$(term sgr0)"
fi

usage () {
	echo "${GREEN}Usage:${NORM} [ENV_VAR=setting] ... ${0##*/} [options] <scenario.cfg>"
	echo ""
	echo "Start scenario defined in <scenario.cfg>"
	echo ""
	echo "${GREEN}Options:${NORM}"
	echo "  ${BOLD}-h${NORM}, ${BOLD}--help${NORM}    show this help message and exit"
	echo "  ${BOLD}-I${NORM}, ${BOLD}--ignore${NORM}  Ignore missing files"
	echo ""
	echo "${GREEN}Example:${NORM}"
	echo ""
	echo "  # start scenario with default options"
	echo "  ./utils/start-test.sh scenarios/autotest-090-master-no-samba.cfg"
	echo ""
	echo "  # start scenario with docker mode on KVM server 'tross'"
	echo "  KVM_BUILD_SERVER=tross DOCKER=true ./utils/start-test.sh scenarios/autotest-090-master-no-samba.cfg"
	echo ""
	echo "${GREEN}Environment variables:${NORM}"
	echo "  Environment variables marked '<' are used to modify the default behavior."
	echo "  Several additional variables marked '>' get derived and exported."
	echo "  Other variables marked '|' get just passed through."
	echo "  All can also be referenced in the .cfg file via [ENV:name]."
	echo "  The key 'environment:' in each VM section gets exported to the VM (UCS)."
	echo ""
	echo "  EC2"
	echo "    <>${BOLD}CURRENT_AMI${NORM}          - the EC2 AMI for the current UCS release (default: $current_ami)"
	echo "    <>${BOLD}OLD_AMI${NORM}              - the EC2 AMI for the release before the current (default: $old_ami)"
	echo ""
	echo "  UCS"
	echo "    <>${BOLD}TARGET_VERSION${NORM}       - the version to expect to update during update tests (default: $release)"
	echo "    <>${BOLD}UCS_VERSION${NORM}          - the current UCS version (default: $release)"
	echo "     >${BOLD}UCS_MINORRELEASE${NORM}     - the current minor version (default: ${release%%-*})"
	echo "    <>${BOLD}OLD_VERSION${NORM}          - the UCS version before the current UCS release (default: $old_release)"
	echo ""
	echo "  KVM"
	echo "    <>${BOLD}KVM_TEMPLATE${NORM}         - the KVM template to use (default: $kvm_template)"
	echo "    <>${BOLD}KVM_UCSVERSION${NORM}       - the KVM template version (default: $kvm_template_version)"
	echo "    <>${BOLD}KVM_OLDUCSVERSION${NORM}    - the KVM template version for the UCS release before the current release (default: $old_release)"
	echo "    <>${BOLD}KVM_BUILD_SERVER${NORM}     - the KVM build server to use (default: $kvm_build_server)"
	echo "    <>${BOLD}KVM_MEMORY${NORM}           - RAM for the KVM instance (default: $kvm_memory)"
	echo "    <>${BOLD}KVM_CPUS${NORM}             - CPU's for the KVM instance (default: $kvm_cpus)"
	echo "    <>${BOLD}KVM_LABEL_SUFFIX${NORM}     - additional label for instance name (default: $kvm_label_suffix)"
	echo "    | ${BOLD}KVM_KEYPAIR_PASSPHRASE${NORM} - ssh key password, also used as a fallback password for the ssh connection"
	echo "    <>${BOLD}SOURCE_ISO${NORM}           - an ISO to mount (default: $source_iso)"
	echo ""
	echo "  ucs-*-create"
	echo "    <>${BOLD}EXACT_MATCH${NORM}          - if true, add -e (only look for exact matches in template names) (default: $exact_match)"
	echo "    <>${BOLD}SHUTDOWN${NORM}             - if true, add -s (shutdown VMs after run) (default: $shutdown)"
	echo "    <>${BOLD}TERMINATE${NORM}            - if true, add -t (Remove VMs after run) (default: false)"
	echo "    <>${BOLD}TERMINATE_ON_SUCCESS${NORM} - if true, add --terminate-on-success (Remove VMs after run only if setup has been successful, true for jenkins, otherwise false)"
	echo "                           (default: true for jenkins, otherwise false)"
	echo "    <>${BOLD}REPLACE${NORM}              - if true, add --replace (if set, overwrite previous VMs with same name)"
	echo "                           (default: true for jenkins, otherwise false)"
	echo ""
	echo "  update behaviour/dev or released version"
	# TODO make the env var a captial letter, -> modify jenkins seed job(s) and cfg files
	echo "    <>${BOLD}release_update${NORM}       - public, testing or none for release updates (default: public)"
	# TODO see RELEASE_UPDATE
	echo "    <>${BOLD}errata_update${NORM}        - public, testing or none for errata updates (default: testing)"
	echo "    <>${BOLD}UCSSCHOOL_RELEASE${NORM}    - UCS@school release (default: $ucsschool_release)"
	echo "    <>${BOLD}COMPONENT_VERSION${NORM}    - update component? should indicate dev/released version of non UCS component (app, ...) (default: testing)"
	echo "    | ${BOLD}SCOPE${NORM}                - defines a extra apt repo/scope that can be included during the test (default: None)"
	echo "    | ${BOLD}TESTING${NORM}              - indicates unreleased UCS version (e.g. testing)"
	echo ""
	echo "  ucs-test/fetch-results"
	echo "    <>${BOLD}UCS_TEST_RUN${NORM}         - if true, start ucs-test in utils/utils.sh::run_tests and copy log files from instance"
	echo "                           in utils/utils-local.sh::fetch-results (default: true for jenkins, otherwise false)"
	echo ""
	echo "  internal"
	echo "    <>${BOLD}DOCKER${NORM}               - use docker container instead if local ucs-ec2-tools (default: true)"
	echo "    < ${BOLD}DIMAGE${NORM}               - docker image (default: ${DIMAGE:--})"
	echo "    <>${BOLD}DEBUG${NORM}                - debug mode (default: ${DEBUG:--})"
	echo ""
	echo "  branch tests:"
	echo "    < ${BOLD}UCSSCHOOL_BRANCH${NORM}     - Name of U@S git branch to build"
	echo "    < ${BOLD}UCS_BRANCH${NORM}           - Name of UCS git branch to build"
	echo ""
	echo "  apps"
	echo "    | ${BOLD}APP_ID${NORM}               - An app ID, wekan"
	echo "    | ${BOLD}COMBINED_APP_ID${NORM}      - ???"
}

die () {
	echo "${RED}$*${NORM}" >&2
	exit 1
}

cleanup () {
	"$debug" ||
		rm -f "$docker_env_file"
}

trap cleanup EXIT

# read arguments
opts=$(getopt \
	--longoptions "help,ignore" \
	--name "$(basename "$0")" \
	--options "hI" \
	-- "$@"
) || die "see -h|--help"
eval set -- "$opts"
check_missing=true
while true
do
	case "$1" in
		-h|--help)
			usage
			exit 0
			;;
		-I|--ignore)
			check_missing=false
			shift
			;;
		--)
			shift
			break
			;;
	esac
done
[ -n "${1:-}" ] ||
	die "Missing test configuration file!"
CFG="$(readlink -f "$1")"
[ -s "$CFG" ] ||
	die "Missing test configuration file '$CFG'!"

if "$check_missing"
then
	[ -f ~/ec2/scripts/activate-errata-test-scope.sh ] ||
		die "Missing script ~/ec2/scripts/activate-errata-test-scope.sh to activate test errata repo!"
	[ -f ~/ec2/license/license.secret ] ||
		die "Missing secret file ~/ec2/license/license.secret for getting test license!"
	[ -f ~/ec2/keys/tech.pem ] ||
		die "Missing key file ~/ec2/keys/tech.pem to access instances!"
fi
[ -d ./utils ] ||
	cd "${0%/*}/../utils/.." ||
	! "$check_missing" ||
	die "./utils dir is missing!"

export CURRENT_AMI=${CURRENT_AMI:=$current_ami}
export OLD_AMI=${OLD_AMI:=$old_ami}
export UCS_MINORRELEASE="${release%%-*}"
export TARGET_VERSION="${TARGET_VERSION:=$release}"
export UCS_VERSION="${UCS_VERSION:=$release}"
export OLD_VERSION="${OLD_VERSION:=$old_release}"
export KVM_TEMPLATE="${KVM_TEMPLATE:=$kvm_template}"
export KVM_UCSVERSION="${KVM_UCSVERSION:=$kvm_template_version}"
export KVM_OPERATING_SYSTEM="${KVM_OPERATING_SYSTEM:=$kvm_operating_system}"
export KVM_OLDUCSVERSION="${KVM_OLDUCSVERSION:=$old_release}"
export KVM_BUILD_SERVER="${KVM_BUILD_SERVER:=$kvm_build_server}"
export KVM_MEMORY="${KVM_MEMORY:=$kvm_memory}"
export KVM_CPUS="${KVM_CPUS:=$kvm_cpus}"
export KVM_LABEL_SUFFIX="${KVM_LABEL_SUFFIX:=$kvm_label_suffix}"
export EXACT_MATCH="${EXACT_MATCH:=$exact_match}"
export SHUTDOWN="${SHUTDOWN:=$shutdown}"
export RELEASE_UPDATE="${release_update:=public}"
export ERRATA_UPDATE="${errata_update:=testing}"
export COMPONENT_VERSION="${COMPONENT_VERSION:=testing}"
export UCSSCHOOL_RELEASE=${UCSSCHOOL_RELEASE:=$ucsschool_release}
export OPENSTACK_IMAGE_NAME="${OPENSTACK_IMAGE_NAME:=$openstack_image_name}"
export SOURCE_ISO="${SOURCE_ISO:=$source_iso}"

# get image from cfg if not explicitly as env var
if [ -z "$DIMAGE" ]; then
	i="$(sed -n 's/^docker_image: //p' "$CFG")"
	[ -n "$i" ] && image="$i"
fi

# Jenkins defaults
if [ -n "${JENKINS_HOME:-}" ]
then
	export UCS_TEST_RUN="${UCS_TEST_RUN:=true}"
	export TERMINATE="${TERMINATE:=false}"
	export KVM_USER="build"
	# in Jenkins do not terminate VMs if setup is broken,
	# so we can investigate the situation and use replace
	# to overwrite old VMs, also the option there is called HALT
	export TERMINATE_ON_SUCCESS="${TERMINATE_ON_SUCCESS:=$HALT}"
	export REPLACE="${REPLACE:=true}"
else
	export TERMINATE="${TERMINATE:=false}"
	export UCS_TEST_RUN="${UCS_TEST_RUN:=false}"
	export KVM_USER="${KVM_USER:=$USER}"
	export TERMINATE_ON_SUCCESS="${TERMINATE_ON_SUCCESS:=false}"
	export REPLACE="${REPLACE:=false}"
fi


# if the default branch of UCS@school is given, then build UCS else build UCS@school
build_git () {
	local build_branch build_repo
	if [[ "$UCSSCHOOL_BRANCH" = [0-9].[0-9] ]]
	then
		build_branch="$UCS_BRANCH"
		build_repo='git@git.knut.univention.de:univention/ucs.git'
	else
		build_branch="$UCSSCHOOL_BRANCH"
		build_repo='git@git.knut.univention.de:univention/ucsschool.git'
	fi
	# check branch test
	ssh jenkins@buildvm.knut.univention.de /home/jenkins/build -r "${build_repo}" -b "${build_branch}" > utils/apt-get-branch-repo.list ||
		die 'Branch build failed'
	sed -i '/^deb /!d' utils/apt-get-branch-repo.list
}
[ -n "${UCSSCHOOL_BRANCH}${UCS_BRANCH}" ] &&
	build_git

# create the command and run in EC2, OpenStack or KVM depending on cfg
exe="ucs-kvm-create"

# build server can be overwritten per cfg file `build_server`
build_server="$(grep '^\w*build_server:' "$CFG" | awk -F ": " '{print $2}')"
[ -n "$build_server" ] && KVM_BUILD_SERVER="$build_server"

[ "$KVM_BUILD_SERVER" = "EC2" ] && exe="ucs-ec2-create"
[ "$KVM_BUILD_SERVER" = "Openstack" ] && exe="ucs-openstack-create"

if [ "$exe" = "ucs-ec2-create" ]
then
	[ -f ~/.boto ] ||
		die "Missing ~/.boto file for EC2 access!"
fi

# start the test
declare -a cmd=()
if "$docker"
then
	# get latest version of image
	case "$image" in *.*/*) docker pull "$image" ;; esac
	# create env file
	{
		# get aws credentials
		[ "$exe" = "ucs-ec2-create" ] &&
			sed -rne '/^\[Credentials\]/,${/^\[Credentials\]/d;s/^ *(aws_(secret_)?access_key(_id)?) *= *(.*)/\U\1\E=\4/p;/^\[/q}' ~/.boto
		echo "AWS_DEFAULT_REGION=eu-west-1"
		env |
			grep -Eve '^(HOSTNAME|PATH|PWD|OLDPWD|SHELL|SHLVL|TEMP|TEMPDIR|TMPDIR)=|^(KDE|GTK[0-9]*|QT|XDG)_'
	} >"$docker_env_file"
	# TODO add ~/ec2/keys/tech.pem via env
	# TODO add personal ssh key for kvm server access via env

	# docker command
	cmd+=(
		"docker" "run"
		--rm
		-w /test
		-v "${PWD:-$(pwd)}:/test"
		-v "$HOME/ec2:$HOME/ec2:ro"
		-v "$CFG:$CFG:ro"
		--network host
		-u "${UID:-$(id -u)}"
		--env-file "$docker_env_file"
		--security-opt seccomp:unconfined
	)
	# paramiko-2.4 from Debian-10-Buster is too old to handle the new OpenSSH-7.x private key format generated by default by `ssh-keygen`.
	# Use `ssh-keygen -m PEM` or update to Paramiko-2.7!
	# If the private key is encrypted, KVM_PASSWORD must be passed with the passphrase. Because of that default to pass the ssh-agent into the Docker container.
	if [ -n "${SSH_AUTH_SOCK:-}" ]
	then
		cmd+=(
			-v "$SSH_AUTH_SOCK:/.ssh"
			-e 'SSH_AUTH_SOCK=/.ssh'
		)
	else
		cmd+=(
			-v "$HOME/.ssh:$HOME/.ssh:ro"
		)
	fi
	if [ "$exe" = "ucs-openstack-create" ]; then
		for p in ${OS_CLIENT_CONFIG_FILE:+"$OS_CLIENT_CONFIG_FILE"} "${PWD}/clouds.yaml" "${HOME}/.config/openstack/clouds.yaml" /etc/openstack/clouds.yaml
		do
			[ -r "$p" ] || continue
			cmd+=(-v "$p:/etc/openstack/clouds.yml:ro")
			break
		done

	fi
	# interactive mode for debug
	$debug && cmd+=("-it")
	# the image to start
	cmd+=("$image")
fi

"$debug" && "$docker" && cmd+=("bash" '-s' '--')

cmd+=("$exe" -c "$CFG")
# TODO, add debug mode as switch by env variable or possibly there will be verbose modes instead
# [ "$exe" = "ucs-openstack-create" ] && cmd+=(--debug)
"$TERMINATE" && cmd+=("-t")
"$REPLACE" && cmd+=("--replace")
"$TERMINATE_ON_SUCCESS" && cmd+=("--terminate-on-success")
"$EXACT_MATCH" && cmd+=("-e")
"$SHUTDOWN" && cmd+=("-s")

echo "${BLUE}Starting test"
sort -s -t= -k1 <"$docker_env_file"
echo "${cmd[*]}${NORM}"

if [ -n "$JOB_URL" ]; then
	header="$JOB_URL+++++++++++++++++++++++++++++++++++"
	printf "%${#header}s\n" | tr " " "+"
	echo "+ Jenkins Workspace: ${JOB_URL}ws           +"
	echo "+ Jenkins Workspace/test: ${JOB_URL}ws/test +"
	printf "%${#header}s\n" | tr " " "+"
fi

exec "${cmd[@]}"
