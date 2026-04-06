"""NIC validation for the operator-side e-stop client."""

from dataclasses import dataclass
import fcntl
import os
import socket
import struct
from typing import List


IFF_UP = 0x1
SIOCGIFFLAGS = 0x8913
SIOCGIFADDR = 0x8915


@dataclass(frozen=True)
class InterfaceSnapshot:
    name: str
    is_up: bool
    ipv4_addresses: List[str]
    excluded: bool


@dataclass(frozen=True)
class NicValidationResult:
    valid: bool
    error_reason: str
    detected_interfaces: List[InterfaceSnapshot]

    def format_diagnostics(self) -> str:
        if not self.detected_interfaces:
            return "No network interfaces detected."
        lines = []
        for snapshot in self.detected_interfaces:
            address_text = ",".join(snapshot.ipv4_addresses) if snapshot.ipv4_addresses else "-"
            lines.append(
                f"{snapshot.name}: up={snapshot.is_up} ipv4={address_text} "
                f"excluded={snapshot.excluded}"
            )
        return "\n".join(lines)


def _list_interfaces() -> List[str]:
    return sorted(os.listdir("/sys/class/net"))


def _is_up(interface_name: str) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        request = struct.pack("256s", interface_name[:15].encode("utf-8"))
        response = fcntl.ioctl(sock.fileno(), SIOCGIFFLAGS, request)
        flags = struct.unpack("H", response[16:18])[0]
        return bool(flags & IFF_UP)
    except OSError:
        return False
    finally:
        sock.close()


def _get_ipv4_addresses(interface_name: str) -> List[str]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        request = struct.pack("256s", interface_name[:15].encode("utf-8"))
        response = fcntl.ioctl(sock.fileno(), SIOCGIFADDR, request)
        return [socket.inet_ntoa(response[20:24])]
    except OSError:
        return []
    finally:
        sock.close()


def validate_nic(expected: str, exclude_prefixes: List[str]) -> NicValidationResult:
    snapshots: List[InterfaceSnapshot] = []
    for interface_name in _list_interfaces():
        excluded = (
            interface_name != expected
            and interface_name != "lo"
            and any(interface_name.startswith(prefix) for prefix in exclude_prefixes)
        )
        snapshots.append(
            InterfaceSnapshot(
                name=interface_name,
                is_up=_is_up(interface_name),
                ipv4_addresses=_get_ipv4_addresses(interface_name),
                excluded=excluded,
            )
        )

    expected_snapshot = next(
        (snapshot for snapshot in snapshots if snapshot.name == expected),
        None,
    )
    if expected_snapshot is None:
        return NicValidationResult(
            False, f"Expected NIC '{expected}' was not found.", snapshots
        )
    if not expected_snapshot.is_up:
        return NicValidationResult(False, f"Expected NIC '{expected}' is not UP.", snapshots)
    if not expected_snapshot.ipv4_addresses:
        return NicValidationResult(
            False,
            f"Expected NIC '{expected}' has no IPv4 address.",
            snapshots,
        )

    active_others = [
        snapshot
        for snapshot in snapshots
        if snapshot.name not in ("lo", expected)
        and not snapshot.excluded
        and snapshot.is_up
        and snapshot.ipv4_addresses
    ]
    if active_others:
        other_names = ", ".join(snapshot.name for snapshot in active_others)
        return NicValidationResult(
            False,
            f"Unexpected active NICs detected: {other_names}.",
            snapshots,
        )

    return NicValidationResult(True, "", snapshots)
