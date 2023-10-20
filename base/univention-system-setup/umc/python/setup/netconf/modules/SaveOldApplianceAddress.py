from typing import Dict, Optional, TypeVar

from univention.management.console.modules.setup.netconf.conditions import AddressChange, SkipPhase


_V = TypeVar("_V")


class PhaseSaveOldApplianceAddress(AddressChange):
    """Save old IP address in dummy interface to not dis-connect the UMC connection."""

    priority = 1

    def check(self) -> None:
        super(PhaseSaveOldApplianceAddress, self).check()
        if not self.changeset.options.appliance_mode:
            raise SkipPhase("Save only in appliance-mode")

    def pre(self) -> None:
        super(PhaseSaveOldApplianceAddress, self).pre()
        new_ipv4s = {iface.ip for iface in self.changeset.new_ipv4s}
        for name, iface in self.changeset.old_interfaces.ipv4_interfaces:
            if ':' in name:
                self.logger.info("Skipping %s...", name)
            ipv4 = iface.ipv4_address().ip
            if ipv4 not in new_ipv4s:
                self.rewrite(name, iface)

    def rewrite(self, name: str, iface: Dict[str, str]) -> None:
        self.logger.info("Rewriting %s=%r...", name, iface)
        tmp_iface = self._copy_iface(iface)
        new_name = self.find_next_interface(name)
        new_iface = self._prefix_iface(new_name, tmp_iface)
        self.logger.debug("Rewrite: %s=%r", new_name, new_iface)
        self.changeset.update_config(new_iface)

    @staticmethod
    def _copy_iface(iface: Dict[str, str]) -> Dict[str, Optional[str]]:
        tmp_iface: Dict[str, Optional[str]] = {
            "type": "appliance-mode-temporary",
        }
        for key in ("address", "network", "netmask", "broadcast"):
            tmp_iface[key] = iface.get(key, None)
        return tmp_iface

    @staticmethod
    def _prefix_iface(prefix: str, iface: Dict[str, _V]) -> Dict[str, _V]:
        new_iface = {
            f"interfaces/{prefix}/{key}": value
            for key, value in iface.items()
        }
        return new_iface

    def find_next_interface(self, base: str) -> str:
        names = self.changeset.new_names
        i = 0
        while "%s:%d" % (base, i) in names:
            i += 1
        return "%s_%d" % (base, i)
