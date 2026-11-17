import re
from dataclasses import dataclass
from typing import List, Optional

# High-priority package prefixes and names to highlight
CORE_PACKAGES = {
    "linux",
    "linux-lts",
    "linux-zen",
    "linux-hardened",
    "linux-cachyos",
    "linux-cachyos-bore",
    "systemd",
    "glibc",
    "mesa",
    "vulkan-radeon",
    "nvidia",
    "nvidia-utils",
    "pipewire",
    "wireplumber",
    "wayland",
    "xorg-server",
    "xorg-xwayland",
    "plasma-desktop",
    "gnome-shell",
    "hyprland",
    "sway",
    "openssl",
    "ca-certificates-mozilla",
    "firefox",
    "chromium",
    "pacman",
    "dbus",
    'niri',
    'zen-browser-bin',
}


@dataclass
class PackageUpdate:
    name: str
    old_version: str
    new_version: str
    source: str = "repo"  # 'repo' or 'aur'
    is_major: bool = False

    @property
    def display_diff(self) -> str:
        return f"{self.old_version} -> {self.new_version}"


def parse_package_line(line: str, default_source: str = "repo") -> Optional[PackageUpdate]:
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    source = default_source
    if line.startswith("[repo]"):
        source = "repo"
        line = line[6:].strip()
    elif line.startswith("[aur]"):
        source = "aur"
        line = line[5:].strip()

    # Match: <pkgname> <old_ver> -> <new_ver> 
    match = re.match(r"^(\S+)\s+(\S+)\s+->\s+(\S+)", line)
    if not match:
        return None

    name, old_ver, new_ver = match.group(1), match.group(2), match.group(3)

    # Determine if this is a major version bump
    is_major = check_major_bump(old_ver, new_ver)

    return PackageUpdate(
        name=name,
        old_version=old_ver,
        new_version=new_ver,
        source=source,
        is_major=is_major,
    )


def check_major_bump(old_ver: str, new_ver: str) -> bool:
    # Strip epoch (e.g. 1:2.0 -> 2.0)
    clean_old = old_ver.split(":", 1)[-1]
    clean_new = new_ver.split(":", 1)[-1]

    old_parts = re.split(r"[.\-_]", clean_old)
    new_parts = re.split(r"[.\-_]", clean_new)

    if old_parts and new_parts:
        if old_parts[0].isdigit() and new_parts[0].isdigit():
            if int(new_parts[0]) > int(old_parts[0]):
                return True
        elif len(old_parts) > 1 and len(new_parts) > 1:
            if old_parts[0] == new_parts[0] and old_parts[1].isdigit() and new_parts[1].isdigit():
                if int(new_parts[1]) > int(old_parts[1]):
                    return True
    return False


def prioritize_packages(packages: List[PackageUpdate]) -> List[PackageUpdate]:
    """Sort packages so core components and major bumps come first."""
    def score(pkg: PackageUpdate) -> int:
        points = 0
        if pkg.name in CORE_PACKAGES or any(pkg.name.startswith(c) for c in ("linux-", "nvidia", "mesa", "systemd")):
            points += 100
        if pkg.is_major:
            points += 30
        if pkg.source == "repo":
            points += 10
        return points

    return sorted(packages, key=score, reverse=True)

