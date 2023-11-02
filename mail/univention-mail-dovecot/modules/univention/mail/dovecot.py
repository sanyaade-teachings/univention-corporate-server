#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Mail Dovecot - shared code for listeners
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2015-2023 Univention GmbH
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

from __future__ import annotations
import grp
import os
import os.path
import pwd
import re
import shutil
import stat
import subprocess
import traceback


try:
    from typing import Any, Optional, Sequence, Tuple  # noqa: F401
except ImportError:
    pass

import univention.debug as ud


default_sieve_script = "/var/lib/dovecot/sieve/default.sieve"


class DovecotListener(object):

    def __init__(self, listener, name):
        # type: (str) -> None
        self.listener = listener
        self.name = name

    def log_p(self, msg: str) -> None:
        ud.debug(ud.LISTENER, ud.PROCESS, f"{self.name}: {msg}")

    def log_e(self, msg: str) -> None:
        ud.debug(ud.LISTENER, ud.ERROR, f"{self.name}: {msg}")

    def new_email_account(self, email: str) -> None:
        spam_folder = self.listener.configRegistry.get("mail/dovecot/folder/spam")
        if self.listener.configRegistry.is_true("mail/dovecot/sieve/spam", True)\
                and spam_folder and spam_folder.lower() != "none":
            try:
                self.upload_activate_sieve_script(email, default_sieve_script)
            except Exception:
                self.log_e(f"dovecot: Could not upload sieve script to account '{email}'.")
                raise
            finally:
                self.listener.unsetuid()

    def delete_email_account(self, dn: str, email: str) -> None:
        if self.listener.configRegistry.is_true('mail/dovecot/mailbox/delete', False):
            try:
                old_localpart, old_domainpart = email.split("@")
                global_mail_home = self.get_maillocation()
                old_home_calc = str(global_mail_home).replace("%Ld", old_domainpart).replace("%Ln", old_localpart)
            except Exception:
                self.log_e(f"dovecot: Delete mailbox: Configuration error. Could not remove mailbox (dn:'{dn}' old mail: '{email}').")
                raise
            self.read_from_ext_proc_as_root(["/usr/bin/doveadm", "kick", email])
            try:
                self.listener.setuid(0)
                shutil.rmtree(old_home_calc, ignore_errors=True)
            except Exception:
                self.log_e(f"dovecot: Delete mailbox: Error removing directory '{old_home_calc}' from disk.")
                raise
            finally:
                self.listener.unsetuid()
        else:
            self.log_p(f"dovecot: Deleting of mailboxes disabled, not removing '{email}' (dn '{dn}').")

    def read_from_ext_proc_as_root(self, cmd, regexp=None, stdin=None, stdout=subprocess.PIPE, stderr=None, stdin_input=None):
        # type; (Sequence[str], Optional[str], Optional[str], Any, Any, Any) -> str
        """
        Wrapper around Popen(), runs external command as root and return its
        output, optionally the first hit of a regexp. May raise an exception.

        :param cmd: list: with executable path as first item
        :param regexp: string: regexp for re.findall()
        :return: string
        """
        try:
            self.listener.setuid(0)
            cmd_proc = subprocess.Popen(cmd, stdin=stdin, stdout=stdout, stderr=stderr)
            cmd_out, cmd_err = cmd_proc.communicate(input=stdin_input and stdin_input.encode('UTF-8'))
            cmd_exit = cmd_proc.wait()
            if cmd_out and not cmd_err and cmd_exit == 0:
                if regexp:
                    res = re.findall(regexp, cmd_out.decode('UTF-8'))
                    return res[0]
                else:
                    return cmd_out.decode('UTF-8').rstrip()
        finally:
            self.listener.unsetuid()

    def move_user_home(self, newMailPrimaryAddress: str, oldMailPrimaryAddress: str, force_rename: bool=False) -> None:
        if not force_rename and not self.listener.configRegistry.is_true("mail/dovecot/mailbox/rename", False):
            self.log_p(f"Renaming of mailboxes disabled, not moving ('{oldMailPrimaryAddress}' -> '{newMailPrimaryAddress}').")
            return

        old_localpart, old_domainpart = oldMailPrimaryAddress.lower().split("@")

        try:
            global_mail_home = self.get_maillocation()
            old_home_calc = str(global_mail_home).replace("%Ld", old_domainpart).replace("%Ln", old_localpart)
            new_home_dove = self.get_user_home(newMailPrimaryAddress)
        except Exception:
            self.log_e(f"Move mailbox: Configuration error. Could not move mailbox ('{oldMailPrimaryAddress}' -> '{newMailPrimaryAddress}').")
            return

        try:
            self.listener.setuid(0)
            if not os.path.isdir(old_home_calc):
                # Either the user never logged in or never got any email, and thus no maildir was ever created,
                # or it was moved manually. In any case: ignore.
                self.log_p(f"Move mailbox: Source directory ('{old_home_calc}') does not exist. Nothing to do for mailbox move ('{oldMailPrimaryAddress}' -> '{newMailPrimaryAddress}').")
                return
            if os.path.isdir(new_home_dove) or os.path.isfile(new_home_dove):
                # We don't know why there is a file or directory already. For security reasons we don't do anything.
                self.log_e(f"Move mailbox: Target directory ('{new_home_dove}') exists.  For security reasons not moving mailbox for mailbox move ('{oldMailPrimaryAddress}' -> '{newMailPrimaryAddress}').")
                return
        finally:
            self.listener.unsetuid()

        try:
            self.read_from_ext_proc_as_root(["/usr/bin/doveadm", "kick", oldMailPrimaryAddress])
        except Exception:
            # ignore
            pass

        try:
            self.move_mail_home(old_home_calc, new_home_dove, newMailPrimaryAddress, force_rename)
        except Exception:
            self.log_e(f"Move mailbox: Failed to move mail home (of mail '{newMailPrimaryAddress}') from '{old_home_calc}' to '{new_home_dove}'.\n{traceback.format_exc()}")
            return

        self.log_p(f"Moved mail home (of mail: '{newMailPrimaryAddress}') from '{old_home_calc}' to '{new_home_dove}'.")
        return

    def move_mail_home(self, old_path: str, new_path: str, email: str, force_rename: bool=False) -> None:
        # create parent path in any case to make sure it has correct ownership
        self.mkdir_p(os.path.dirname(new_path))
        if not force_rename and not self.listener.configRegistry.is_true("mail/dovecot/mailbox/rename", False):
            self.log_p(f"Renaming of mailboxes disabled, not moving mail home (of mail '{email}') from '{old_path}' to '{new_path}.")
            return
        try:
            self.listener.setuid(0)
            st = os.stat(old_path)
            shutil.move(old_path, new_path)
            self.chown_r(new_path, st[stat.ST_UID], st[stat.ST_GID])
        except Exception:
            self.log_e(f"Failed to move mail home (of mail '{email}') from '{old_path}' to '{new_path}'.\n{traceback.format_exc()}")
            raise
        finally:
            self.listener.unsetuid()

    def get_maillocation(self) -> str:
        try:
            return self.read_from_ext_proc_as_root(["/usr/bin/doveconf", "-h", "mail_location"], r"\S+:(\S+)/Maildir")
        except Exception:
            self.log_e(f"Failed to get mail_location from Dovecot configuration.\n{traceback.format_exc()}")
            raise

    def upload_activate_sieve_script(self, email: str, file: str) -> None:
        try:
            master_name, master_pw = self.get_masteruser_credentials()
            ca_file = self.listener.configRegistry.get("mail/dovecot/sieve/client/cafile", "/etc/univention/ssl/ucsCA/CAcert.pem")
            fqdn = "%(hostname)s.%(domainname)s" % self.listener.configRegistry
            fqdn = self.listener.configRegistry.get("mail/dovecot/sieve/client/server", fqdn)
            _cmd = [
                "sieve-connect", "--user", f"{email}*{master_name}",
                "--server", fqdn,
                "--noclearauth", "--noclearchan",
                "--tlscafile", ca_file,
                "--remotesieve", "default"]
            cmd_upload = list(_cmd)
            cmd_upload.extend(["--localsieve", file, "--upload"])
            self.read_from_ext_proc_as_root(cmd_upload, stdin=subprocess.PIPE, stdin_input=master_pw)
            cmd_activate = list(_cmd)
            cmd_activate.extend(["--activate"])
            self.read_from_ext_proc_as_root(cmd_activate, stdin=subprocess.PIPE, stdin_input=master_pw)
        except Exception:
            self.log_e(f"upload_activate_sieve_script(): Could not upload sieve script '{file}' to mailbox '{email}'. Exception:\n{traceback.format_exc()}")
            raise

    def get_user_home(self, username: str) -> str:
        try:
            return self.read_from_ext_proc_as_root(["/usr/bin/doveadm", 'user', "-f", "home", username]).lower()
        except Exception:
            self.log_e(f"Failed to get mail home for user '{username}'.\n{traceback.format_exc()}")
            raise

    def get_masteruser_credentials(self) -> Tuple[str, str]:
        try:
            self.listener.setuid(0)
            return re.findall(r"(\S+):{PLAIN}(\S+)::::::", open("/etc/dovecot/master-users").read())[0]
        except Exception:
            self.log_e(f"Failed to get masteruser password.\n{traceback.format_exc()}")
            raise
        finally:
            self.listener.unsetuid()

    def get_dovecot_user(self) -> Tuple[str, str]:
        if not hasattr(self, "dovecot_user") or not hasattr(self, "dovecot_group"):
            try:
                uid = self.read_from_ext_proc_as_root(["/usr/bin/doveconf", "-h", "mail_uid"])
                gid = self.read_from_ext_proc_as_root(["/usr/bin/doveconf", "-h", "mail_gid"])
            except Exception:
                uid = "dovemail"
                gid = "dovemail"
            self.dovecot_user = uid
            self.dovecot_group = gid
        return self.dovecot_user, self.dovecot_group

    def mkdir_p(self, dir: str) -> None:
        user, group = self.get_dovecot_user()
        dovecot_uid = pwd.getpwnam(user).pw_uid
        dovecot_gid = grp.getgrnam(group).gr_gid
        # spool directory has to be traversed as root
        self.listener.setuid(0)
        parent = os.path.dirname(dir)
        if not os.path.exists(parent):
            self.listener.unsetuid()
            self.mkdir_p(parent)
        else:
            self.listener.unsetuid()

        try:
            self.listener.setuid(0)
            if not os.path.exists(dir):
                os.mkdir(dir, 0o2700)
                os.chown(dir, dovecot_uid, dovecot_gid)
        except Exception:
            self.log_e(f"Failed to create directory '{dir}'.\n{traceback.format_exc()}")
            raise
        finally:
            self.listener.unsetuid()

    @classmethod
    def chown_r(cls, path: str, uid: int, gid: int) -> None:
        """
        Recursively set owner and group on a file/directory and its
        subdirectories.

        :param str path: file/directory (and its subdirectories) to change ownership on
        :param int uid: UID to set
        :param int gid: GID to set
        :return: None
        """
        def chown_if_different(path_, uid_, gid_):
            st = os.stat(path_)
            if st[stat.ST_UID] != uid_ or st[stat.ST_GID] != gid_:
                os.chown(path_, uid_, gid_)

        chown_if_different(path, uid, gid)
        for dirpath, dirnames, filenames in os.walk(path):
            for dirname in dirnames:
                cls.chown_r(os.path.join(dirpath, dirname), uid, gid)
            for filename in filenames:
                chown_if_different(os.path.join(dirpath, filename), uid, gid)
