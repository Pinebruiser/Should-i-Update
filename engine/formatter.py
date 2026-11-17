import os
import sys
from typing import Any, Dict, List

# ANSI Color Code Detection
def check_use_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR") in ("1", "true", "True"):
        return True
    return sys.stdout.isatty() or sys.stderr.isatty()


USE_COLOR = check_use_color()

RESET = "\033[0m" if USE_COLOR else ""
BOLD = "\033[1m" if USE_COLOR else ""
DIM = "\033[2m" if USE_COLOR else ""

RED = "\033[31m" if USE_COLOR else ""
GREEN = "\033[32m" if USE_COLOR else ""
YELLOW = "\033[33m" if USE_COLOR else ""
BLUE = "\033[34m" if USE_COLOR else ""
MAGENTA = "\033[35m" if USE_COLOR else ""
CYAN = "\033[36m" if USE_COLOR else ""
GRAY = "\033[90m" if USE_COLOR else ""

BOLD_RED = "\033[1;31m" if USE_COLOR else ""
BOLD_GREEN = "\033[1;32m" if USE_COLOR else ""
BOLD_YELLOW = "\033[1;33m" if USE_COLOR else ""
BOLD_CYAN = "\033[1;36m" if USE_COLOR else ""
BOLD_MAGENTA = "\033[1;35m" if USE_COLOR else ""

CATEGORY_META = {
    "UPNOW": {
        "title": "UPNOW — Critical & Security Patches",
        "color": BOLD_RED,
        "desc_color": RED,
        "description": "Urgent security advisories, core kernels, microcode, or breaking fixes.",
    },
    "COOLFEAT": {
        "title": "COOLFEAT — Notable New Features & Major Releases",
        "color": BOLD_CYAN,
        "desc_color": CYAN,
        "description": "Noticeable enhancements, major version leaps, desktop & application upgrades.",
    },
    "IFYOUWANT": {
        "title": "IFYOUWANT — Routine Maintenance & Minor Fixes",
        "color": BOLD_YELLOW,
        "desc_color": YELLOW,
        "description": "Standard point releases, routine bug fixes, translation updates.",
    },
    "REDUNDANT": {
        "title": "REDUNDANT — Low Priority Rebuilds & Documentation",
        "color": GRAY,
        "desc_color": DIM,
        "description": "Trivial dependency bumps, man pages, localization packs with no user impact.",
    },
}


def render_banner(verdict: str, summary: str, total_pkgs: int) -> str:
    lines = []
    lines.append("")
    divider = "─" * 68

    verdict_str = verdict.upper().replace(" ", "_")
    if "NOW" in verdict_str:
        tag = f"{BOLD_RED}VERDICT: UPGRADE PROMPTLY{RESET}"
    elif "WAIT" in verdict_str or "SAFE" in verdict_str:
        tag = f"{BOLD_GREEN}VERDICT: SAFE TO DEFER{RESET}"
    else:
        tag = f"{BOLD_CYAN}VERDICT: UPGRADE RECOMMENDED{RESET}"

    lines.append(f"{BOLD}╭─ Should-i-Update Analysis {divider[:41]}╮{RESET}")
    lines.append(f"│  {tag}  ({total_pkgs} pending updates total)")
    if summary:
        import textwrap
        for paragraph in summary.strip().splitlines():
            if not paragraph.strip():
                continue
            for s_line in textwrap.wrap(paragraph.strip(), width=64):
                lines.append(f"│  {DIM}{s_line}{RESET}")
    lines.append(f"{BOLD}╰{divider[:67]}╯{RESET}")
    lines.append("")
    return "\n".join(lines)


def render_category(cat_key: str, items: List[Dict[str, Any]]) -> str:
    if not items:
        return ""

    meta = CATEGORY_META.get(cat_key, {
        "title": cat_key,
        "color": BOLD,
        "desc_color": "",
        "description": "",
    })

    lines = []
    header = f"{meta['title']} ({len(items)})"
    lines.append(f"{meta['color']}{header}{RESET}")
    lines.append(f"{DIM}  {meta['description']}{RESET}")

    for item in items:
        pkg = item.get("pkg", "unknown")
        ver = item.get("version", "")
        ver_str = f" {DIM}({ver}){RESET}" if ver else ""
        lines.append(f"  {BOLD}• {pkg}{RESET}{ver_str}")

        if "reason" in item and item["reason"]:
            lines.append(f"    {meta['desc_color']}↳ {item['reason']}{RESET}")

    lines.append("")
    return "\n".join(lines)


def render_report(result: Dict[str, Any], total_pkgs: int) -> str:
    verdict = result.get("verdict", "UPGRADE_RECOMMENDED")
    summary = result.get("summary", "")
    categories = result.get("categories", {})

    output = []
    output.append(render_banner(verdict, summary, total_pkgs))

    for cat_name in ["UPNOW", "COOLFEAT", "IFYOUWANT", "REDUNDANT"]:
        items = categories.get(cat_name, [])
        if items:
            output.append(render_category(cat_name, items))

    # Summary counts
    counts = []
    for cat in ["UPNOW", "COOLFEAT", "IFYOUWANT", "REDUNDANT"]:
        count = len(categories.get(cat, []))
        counts.append(f"{cat}: {count}")

    output.append(f"{DIM}[ {' | '.join(counts)} ]{RESET}\n")
    return "\n".join(output)

