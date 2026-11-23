#!/usr/bin/env bash
# ==============================================================================
# Should-i-Update: Interactive Installer & Setup Wizard
# ==============================================================================
set -eo pipefail

REPO_URL="https://github.com/Pinebruiser/Should-i-Update"
REPO_BRANCH="main"

VERSION="0.1.0-beta.1"

# ANSI Colors
if [[ -t 1 && -z "${NO_COLOR}" ]]; then
    export FORCE_COLOR=1
    C_RESET="\033[0m"
    C_BOLD="\033[1m"
    C_DIM="\033[2m"
    C_RED="\033[31m"
    C_GREEN="\033[32m"
    C_YELLOW="\033[33m"
    C_BLUE="\033[34m"
    C_CYAN="\033[36m"
    C_MAGENTA="\033[35m"
else
    C_RESET=""
    C_BOLD=""
    C_DIM=""
    C_RED=""
    C_GREEN=""
    C_YELLOW=""
    C_BLUE=""
    C_CYAN=""
    C_MAGENTA=""
fi

CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/should-i-update"
CONFIG_PATH="${CONFIG_DIR}/config.json"

get_config_provider() {
    if [[ -f "${CONFIG_PATH}" ]]; then
        python3 -c "import json; cfg = json.load(open('${CONFIG_PATH}')); print(cfg.get('provider', 'gemini'))" 2>/dev/null || echo "gemini"
    else
        echo "gemini"
    fi
}

handle_reset_key() {
    local silent="$1"
    local current_prov="$(get_config_provider)"
    current_prov="$(echo "${current_prov}" | tr '[:upper:]' '[:lower:]')"

    secret-tool clear service should-i-update provider "${current_prov}" 2>/dev/null || true

    if [[ "${silent}" == "--silent" ]]; then
        return 0
    fi

    echo -e "${C_GREEN}✓ API key for current provider (${current_prov}) cleared from Linux Secret Service.${C_RESET}"
    echo -e "\n If you would you like you can:"
    echo -e "  1) Use a different key with the ${C_BOLD}same provider${C_RESET} (${current_prov}):"
    echo -e "     Run: ${C_CYAN}should-i-update --replace-key${C_RESET}"
    echo -e "  2) Switch to a ${C_BOLD}different provider${C_RESET}:"
    echo -e "     Run: ${C_CYAN}should-i-update --change-provider${C_RESET}\n"
    exit 0
}

handle_replace_key() {
    local current_prov="$(get_config_provider)"
    current_prov="$(echo "${current_prov}" | tr '[:upper:]' '[:lower:]')"

    echo -e "${C_CYAN}:: Replace API Key for active provider:${C_RESET} ${C_BOLD}${current_prov}${C_RESET}"
    echo -ne "${C_BOLD}Paste new ${current_prov^^} API key (input hidden): ${C_RESET}"
    if [[ -t 0 ]]; then
        read -rs new_key
        echo ""
    else
        read -r new_key || new_key=""
    fi

    if [[ -z "${new_key}" ]]; then
        echo -e "${C_RED}[!] No key entered. Operation cancelled.${C_RESET}" >&2
        exit 1
    fi

    printf "%s" "${new_key}" | secret-tool store --label="Should-i-Update API Key (${current_prov})" service should-i-update provider "${current_prov}"
    echo -e "${C_GREEN}✓ API key for '${current_prov}' successfully updated in Linux Secret Service.${C_RESET}"
    exit 0
}

handle_change_provider() {
    local old_prov="$(get_config_provider)"

    # Reuse reset-key logic to delete current key and avoid duplicate code
    handle_reset_key --silent

    echo -e "${C_BLUE}==>${C_RESET} ${C_BOLD}Select new LLM Provider:${C_RESET}"
    echo -e "  ${C_CYAN}1)${C_RESET} ${C_BOLD}Google Gemini${C_RESET}   ${C_GREEN}(Free Tier available, fast, recommended)${C_RESET}"
    echo -e "  ${C_CYAN}2)${C_RESET} ${C_BOLD}OpenRouter${C_RESET}      ${C_GREEN}(Auto / Open models, free & paid)${C_RESET}"
    echo -e "  ${C_CYAN}3)${C_RESET} ${C_BOLD}Anthropic Claude${C_RESET} (Claude 3.5 Haiku / Sonnet)"
    echo -e "  ${C_CYAN}4)${C_RESET} ${C_BOLD}OpenAI${C_RESET}          (GPT-4o-mini / GPT-4o)"

    local new_prov=""

    while [[ -z "${new_prov}" ]]; do
        echo -ne "\n${C_BOLD}Select provider [1-4] (default: 1): ${C_RESET}"
        if [[ -t 0 ]]; then
            read -r prov_choice
        else
            read -r prov_choice || prov_choice="1"
        fi
        prov_choice="${prov_choice:-1}"
        case "${prov_choice}" in
            1) new_prov="gemini" ;;
            2) new_prov="openrouter" ;;
            3) new_prov="claude" ;;
            4) new_prov="openai" ;;
            *)
                echo -e "${C_RED}Invalid choice. Please select 1, 2, 3, or 4.${C_RESET}"
                ;;
        esac
    done

    echo -ne "${C_BOLD}Paste your ${new_prov^^} API key (input hidden): ${C_RESET}"
    if [[ -t 0 ]]; then
        read -rs api_key
        echo ""
    else
        read -r api_key || api_key=""
    fi

    if [[ -z "${api_key}" ]]; then
        echo -e "${C_RED}[!] No key entered. Operation cancelled.${C_RESET}" >&2
        exit 1
    fi

    printf "%s" "${api_key}" | secret-tool store --label="Should-i-Update API Key (${new_prov})" service should-i-update provider "${new_prov}"
    echo -e "${C_GREEN}✓ API key saved into Linux Secret Service.${C_RESET}"

    # Update config using engine/config.py to preserve other settings and custom models per provider
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local new_model="$(PYTHONPATH="${script_dir}:${HOME}/.local/share/should-i-update" python3 -c "
from engine.config import set_provider
cfg = set_provider('${new_prov}')
print(cfg.get('curr_model', ''))
")"
    echo -e "${C_GREEN}✓ Provider successfully changed from '${old_prov}' to '${new_prov}' (model: ${new_model})!${C_RESET}"
    exit 0
}

# CLI Argument Parsing
CONFIG_ONLY=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --config-only)
            CONFIG_ONLY=true
            shift
            ;;
        --reset-key)
            handle_reset_key
            ;;
        --replace-key)
            handle_replace_key
            ;;
        --change-provider)
            handle_change_provider
            ;;
        -h|--help)
            echo -e "${C_BOLD}Should-i-Update Installer${C_RESET}"
            echo -e "Usage: install.sh [OPTIONS]"
            echo -e "  --config-only       Reconfigure settings without re-copying files"
            echo -e "  --replace-key       Replace API key for the current active provider"
            echo -e "  --reset-key         Remove current API key from Linux Secret Service"
            echo -e "  --change-provider   Switch LLM provider and configure its API key"
            echo -e "  -h, --help          Show this help message"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

# If stdin is not a terminal (e.g. piped via curl), redirect stdin from /dev/tty for interactive wizard
if [[ ! -t 0 ]]; then
    if [[ -r /dev/tty ]]; then
        exec < /dev/tty
    else
        echo -e "${C_RED}[!] Error: Cannot read from /dev/tty for interactive input.${C_RESET}" >&2
        exit 1
    fi
fi

# Cleanup Trap: If cancelled midway, delete newly stored API key from Secret Service
SETUP_SUCCESS=false
KEY_WAS_NEWLY_STORED=false
SAVED_KEY_PROVIDER=""

cleanup_on_cancel() {
    local exit_code=$?
    if [[ "${SETUP_SUCCESS}" != "true" && "${KEY_WAS_NEWLY_STORED}" == "true" && -n "${SAVED_KEY_PROVIDER}" ]]; then
        echo -e "\n${C_YELLOW}:: Setup was cancelled before completion.${C_RESET}"
        echo -e "   Cleaning up newly stored API key for '${SAVED_KEY_PROVIDER}' from Linux Secret Service..."
        secret-tool clear service should-i-update provider "${SAVED_KEY_PROVIDER}" 2>/dev/null || true
    fi
    exit ${exit_code}
}
trap cleanup_on_cancel INT TERM HUP EXIT

echo -e "${C_CYAN}${C_BOLD}"
cat <<'EOF'
  _____ _                 _     _        _     _             _       _       
 / ____| |               | |   | |      (_)   | |  _   _    | |     | |      
| (___ | |__   ___  _   _| | __| |____-_ _ ___| |_| | | |_ _| | __ _| |_ ___ 
 \___ \| '_ \ / _ \| | | | |/ _` |______|_ / __| __| | | | _` |/ _` | __/ _ \
 ____) | | | | (_) | |_| | | (_| |       | \__ \ |_| |_| | (_| | (_| | ||  __/
|_____/|_| |_|\___/ \__,_|_|\__,_|       |_|___/\__|\__,_|\__,_|\__,_|\__\___|
EOF
echo -e "${C_RESET}"
echo -e "${C_BOLD}Intelligent Arch Linux Package Update Decision Assistant${C_RESET}"
echo -e "${C_DIM}https://github.com/Pinebruiser/Should-i-Update${C_RESET}\n"

# ==============================================================================
# Step 1: Check Dependencies
# ==============================================================================
echo -e "${C_BLUE}==>${C_RESET} ${C_BOLD}[Step 1/6] Checking dependencies...${C_RESET}"

MISSING_PKGS=()

if ! command -v checkupdates &>/dev/null; then
    MISSING_PKGS+=("pacman-contrib")
fi

if ! command -v python3 &>/dev/null; then
    MISSING_PKGS+=("python")
fi

if ! command -v secret-tool &>/dev/null; then
    MISSING_PKGS+=("libsecret")
fi

if [[ ${#MISSING_PKGS[@]} -gt 0 ]]; then
    echo -e "${C_YELLOW}:: The following required packages are missing:${C_RESET} ${MISSING_PKGS[*]}"
    echo -ne "${C_BOLD}Would you like to install them now with sudo pacman? [Y/n]: ${C_RESET}"
    read -r install_dep_choice
    install_dep_choice="${install_dep_choice:-Y}"
    if [[ "${install_dep_choice}" =~ ^[Yy]$ ]]; then
        sudo pacman -S --needed "${MISSING_PKGS[@]}"
    else
        echo -e "${C_RED}[!] Error: Required dependencies must be installed to continue.${C_RESET}" >&2
        exit 1
    fi
else
    echo -e "${C_GREEN}✓ All core dependencies found (pacman-contrib, python, libsecret).${C_RESET}"
fi

# Detect AUR helper
AUR_HELPER=""
if command -v yay &>/dev/null; then
    AUR_HELPER="yay"
elif command -v paru &>/dev/null; then
    AUR_HELPER="paru"
fi

# ==============================================================================
# Step 2: Choose LLM Provider
# ==============================================================================
echo -e "\n${C_BLUE}==>${C_RESET} ${C_BOLD}[Step 2/6] Select LLM Provider:${C_RESET}"
echo -e "  ${C_CYAN}1)${C_RESET} ${C_BOLD}Google Gemini${C_RESET}   ${C_GREEN}(Free Tier available, fast, recommended)${C_RESET}"
echo -e "  ${C_CYAN}2)${C_RESET} ${C_BOLD}OpenRouter${C_RESET}      ${C_GREEN}(Auto / Open models, free & paid)${C_RESET}"
echo -e "  ${C_CYAN}3)${C_RESET} ${C_BOLD}Anthropic Claude${C_RESET} (Claude 3.5 Haiku / Sonnet)"
echo -e "  ${C_CYAN}4)${C_RESET} ${C_BOLD}OpenAI${C_RESET}          (GPT-4o-mini / GPT-4o)"

SELECTED_PROVIDER=""

while [[ -z "${SELECTED_PROVIDER}" ]]; do
    echo -ne "\n${C_BOLD}Select provider [1-4] (default: 1): ${C_RESET}"
    read -r prov_choice
    prov_choice="${prov_choice:-1}"
    case "${prov_choice}" in
        1) SELECTED_PROVIDER="gemini" ;;
        2) SELECTED_PROVIDER="openrouter" ;;
        3) SELECTED_PROVIDER="claude" ;;
        4) SELECTED_PROVIDER="openai" ;;
        *)
            echo -e "${C_RED}Invalid choice. Please select 1, 2, 3, or 4.${C_RESET}"
            ;;
    esac
done

SCRIPT_DIR_LOCAL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SELECTED_MODEL="$(PYTHONPATH="${SCRIPT_DIR_LOCAL}:${HOME}/.local/share/should-i-update" python3 -c "
from engine.config import get_default_model
print(get_default_model('${SELECTED_PROVIDER}'))
" 2>/dev/null || true)"

echo -e "${C_GREEN}✓ Selected: ${SELECTED_PROVIDER} (model: ${SELECTED_MODEL})${C_RESET}"

# ==============================================================================
# Step 3: Keyring Storage & Authentication Setup
# ==============================================================================
echo -e "\n${C_BLUE}==>${C_RESET} ${C_BOLD}[Step 3/6] Authentication Setup:${C_RESET}"
echo -e ":: API keys are saved securely in the ${C_BOLD}Linux Secret Service${C_RESET} (GNOME Keyring / KWallet / KeePassXC)."
echo -e "   ${C_DIM}They persist across reboots and are NEVER stored in plaintext config files.${C_RESET}"

# Check if key is already in secret store
EXISTING_KEY="$(secret-tool lookup service should-i-update provider "${SELECTED_PROVIDER}" 2>/dev/null || true)"
SKIP_KEY_PROMPT=false
if [[ -n "${EXISTING_KEY}" ]]; then
    echo -e "${C_GREEN}✓ Existing key found in Linux Secret Service for ${SELECTED_PROVIDER}.${C_RESET}"
    echo -ne "${C_BOLD}Do you want to replace it? [y/N]: ${C_RESET}"
    read -r replace_key
    if [[ ! "${replace_key}" =~ ^[Yy]$ ]]; then
        SKIP_KEY_PROMPT=true
    fi
fi

if [[ "${SKIP_KEY_PROMPT}" != "true" ]]; then
    echo -ne "${C_BOLD}Paste your ${SELECTED_PROVIDER^^} API key (input hidden): ${C_RESET}"
    read -rs API_KEY
    echo ""

    if [[ -z "${API_KEY}" ]]; then
        echo -e "${C_RED}[!] No key entered. You can set it later using: should-i-update --replace-key${C_RESET}"
    else
        printf "%s" "${API_KEY}" | secret-tool store --label="Should-i-Update API Key (${SELECTED_PROVIDER})" service should-i-update provider "${SELECTED_PROVIDER}"
        KEY_WAS_NEWLY_STORED=true
        SAVED_KEY_PROVIDER="${SELECTED_PROVIDER}"
        echo -e "${C_GREEN}✓ API key saved securely into Linux Secret Service.${C_RESET}"
    fi
fi

# ==============================================================================
# Step 4: LLM Request Timeout
# ==============================================================================
echo -e "\n${C_BLUE}==>${C_RESET} ${C_BOLD}[Step 4/6] LLM Request Timeout:${C_RESET}"
echo -e ":: Request timeout ensures the engine waits long enough for large package batches (300+ updates)."
echo -e "   ${C_DIM}Default is 180 seconds (3 minutes).${C_RESET}"

DEFAULT_TIMEOUT=180
if [[ -f "${CONFIG_PATH}" ]]; then
    DEFAULT_TIMEOUT="$(python3 -c "import json; cfg = json.load(open('${CONFIG_PATH}')); print(cfg.get('request_timeout', 180))" 2>/dev/null || echo 180)"
fi

echo -ne "${C_BOLD}Enter request timeout in seconds [default: ${DEFAULT_TIMEOUT}]: ${C_RESET}"
read -r timeout_choice
timeout_choice="${timeout_choice:-${DEFAULT_TIMEOUT}}"

if [[ "${timeout_choice}" =~ ^[0-9]+$ ]] && [[ ${timeout_choice} -gt 0 ]]; then
    REQUEST_TIMEOUT="${timeout_choice}"
else
    REQUEST_TIMEOUT="${DEFAULT_TIMEOUT}"
fi
echo -e "${C_GREEN}✓ Request timeout set to ${REQUEST_TIMEOUT}s.${C_RESET}"

# ==============================================================================
# Step 5: AUR Packages Preference
# ==============================================================================
echo -e "\n${C_BLUE}==>${C_RESET} ${C_BOLD}[Step 5/6] Arch User Repository (AUR):${C_RESET}"

CHECK_AUR="true"
if [[ -n "${AUR_HELPER}" ]]; then
    echo -e ":: Detected AUR helper: ${C_CYAN}${AUR_HELPER}${C_RESET}"
    echo -ne "${C_BOLD}Would you like Should-i-Update to check AUR packages as well? [Y/n]: ${C_RESET}"
    read -r aur_choice
    aur_choice="${aur_choice:-Y}"
    if [[ ! "${aur_choice}" =~ ^[Yy]$ ]]; then
        CHECK_AUR="false"
    fi
else
    echo -e "${C_DIM}:: No AUR helper (yay/paru) detected. AUR checking will be disabled.${C_RESET}"
    CHECK_AUR="false"
    AUR_HELPER="yay"
fi

# ==============================================================================
# Step 6: System Update Command & Installation
# ==============================================================================
echo -e "\n${C_BLUE}==>${C_RESET} ${C_BOLD}[Step 6/6] Update Command & Setup:${C_RESET}"

HAS_RATE_MIRRORS=false
if command -v cachyos-rate-mirrors &>/dev/null; then
    HAS_RATE_MIRRORS=true
fi

# Build options dynamically based on system capabilities
CMDS=()
DESCS=()
DEFAULT_INDEX=1

if [[ "${HAS_RATE_MIRRORS}" == "true" ]]; then
    if [[ "${CHECK_AUR}" == "true" && -n "${AUR_HELPER}" ]]; then
        CMDS+=("sudo cachyos-rate-mirrors && ${AUR_HELPER} -Syu")
        DESCS+=("Rank fastest mirrors + update official repos & AUR packages")

        CMDS+=("${AUR_HELPER} -Syu")
        DESCS+=("Update official repos & AUR packages (skip mirror rating)")

        CMDS+=("sudo cachyos-rate-mirrors && sudo pacman -Syu")
        DESCS+=("Rank fastest mirrors + update official repos only (no AUR)")

        CMDS+=("sudo pacman -Syu")
        DESCS+=("Standard Arch official update (no mirror rating, no AUR)")
    else
        CMDS+=("sudo cachyos-rate-mirrors && sudo pacman -Syu")
        DESCS+=("Rank fastest mirrors + update official repos")

        CMDS+=("sudo pacman -Syu")
        DESCS+=("Standard Arch official update (skip mirror rating)")
    fi
else
    if [[ "${CHECK_AUR}" == "true" && -n "${AUR_HELPER}" ]]; then
        CMDS+=("${AUR_HELPER} -Syu")
        DESCS+=("Update official repos & AUR packages")

        CMDS+=("sudo pacman -Syu")
        DESCS+=("Standard Arch official update only (no AUR)")
    else
        CMDS+=("sudo pacman -Syu")
        DESCS+=("Standard Arch official update")
    fi
fi

NUM_CMDS=${#CMDS[@]}

echo -e "Choose the command to execute when you confirm updating:"
for i in "${!CMDS[@]}"; do
    idx=$((i + 1))
    cmd="${CMDS[$i]}"
    desc="${DESCS[$i]}"
    if [[ ${idx} -eq ${DEFAULT_INDEX} ]]; then
        echo -e "  ${C_CYAN}${idx})${C_RESET} ${C_BOLD}${cmd}${C_RESET}  ${C_GREEN}[Recommended Default]${C_RESET}"
        echo -e "     ${C_DIM}${desc}${C_RESET}"
    else
        echo -e "  ${C_CYAN}${idx})${C_RESET} ${C_BOLD}${cmd}${C_RESET}"
        echo -e "     ${C_DIM}${desc}${C_RESET}"
    fi
done

UPDATE_CMD=""
while [[ -z "${UPDATE_CMD}" ]]; do
    echo -ne "\n${C_BOLD}Select update command [1-${NUM_CMDS}, default: ${DEFAULT_INDEX}]: ${C_RESET}"
    read -r cmd_choice
    cmd_choice="${cmd_choice:-${DEFAULT_INDEX}}"

    if [[ "${cmd_choice}" =~ ^[0-9]+$ ]] && [[ ${cmd_choice} -ge 1 && ${cmd_choice} -le ${NUM_CMDS} ]]; then
        cmd_idx=$((cmd_choice - 1))
        UPDATE_CMD="${CMDS[$cmd_idx]}"
    elif [[ -n "${cmd_choice}" && ! "${cmd_choice}" =~ ^[0-9]+$ ]]; then
        # Direct string input
        UPDATE_CMD="${cmd_choice}"
    else
        echo -e "${C_RED}Invalid choice. Please select 1-${NUM_CMDS}.${C_RESET}"
    fi
done

echo -e "${C_GREEN}✓ Update command set to:${C_RESET} ${C_BOLD}${UPDATE_CMD}${C_RESET}"

# Write configuration file
mkdir -p "${CONFIG_DIR}"

cat > "${CONFIG_PATH}" <<EOF
{
  "provider": "${SELECTED_PROVIDER}",
  "curr_model": "${SELECTED_MODEL}",
  "saved_models": {
    "${SELECTED_PROVIDER}": "${SELECTED_MODEL}"
  },
  "request_timeout": ${REQUEST_TIMEOUT},
  "check_aur": ${CHECK_AUR},
  "aur_helper": "${AUR_HELPER}",
  "update_command": "${UPDATE_CMD}",
  "check_arch_news": true
}
EOF

echo -e "${C_GREEN}✓ Configuration saved to ${CONFIG_PATH}${C_RESET}"

# If running as --config-only, mark success and exit here
if [[ "${CONFIG_ONLY}" == "true" ]]; then
    SETUP_SUCCESS=true
    echo -e "\n${C_GREEN}${C_BOLD}✓ Configuration updated successfully!${C_RESET}"
    exit 0
fi

# Install files to ~/.local/share/should-i-update and ~/.local/bin
INSTALL_DIR="${HOME}/.local/share/should-i-update"
BIN_DIR="${HOME}/.local/bin"

mkdir -p "${INSTALL_DIR}" "${BIN_DIR}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -d "${SCRIPT_DIR}/engine" ]]; then
    # Local source installation
    cp -r "${SCRIPT_DIR}/engine" "${INSTALL_DIR}/"
    cp "${SCRIPT_DIR}/should-i-update" "${INSTALL_DIR}/"
    cp "${SCRIPT_DIR}/install.sh" "${INSTALL_DIR}/"
else
    # Curled from web: clone or download repository
    echo -e ":: Downloading repository files from GitHub..."
    TMP_CLONE="$(mktemp -d /tmp/should-i-update-clone.XXXXXX)"
    if command -v git &>/dev/null; then
        git clone --depth 1 "${REPO_URL}.git" "${TMP_CLONE}"
    else
        curl -sSL "${REPO_URL}/archive/refs/heads/${REPO_BRANCH}.tar.gz" | tar -xz -C "${TMP_CLONE}" --strip-components=1
    fi
    cp -r "${TMP_CLONE}/engine" "${INSTALL_DIR}/"
    cp "${TMP_CLONE}/should-i-update" "${INSTALL_DIR}/"
    cp "${TMP_CLONE}/install.sh" "${INSTALL_DIR}/"
    rm -rf "${TMP_CLONE}"
fi

chmod +x "${INSTALL_DIR}/should-i-update" "${INSTALL_DIR}/install.sh"
ln -sf "${INSTALL_DIR}/should-i-update" "${BIN_DIR}/should-i-update"

echo -e "${C_GREEN}✓ Installed launcher symlink: ${BIN_DIR}/should-i-update${C_RESET}"

# Verify $PATH
if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    echo -e "\n${C_YELLOW}[!] Note: ${BIN_DIR} is not in your current PATH.${C_RESET}"
    echo -e "    Add it to your shell config (~/.bashrc, ~/.zshrc, or ~/.config/fish/config.fish):"
    echo -e "    ${C_CYAN}export PATH=\"\$HOME/.local/bin:\$PATH\"${C_RESET}"
fi

SETUP_SUCCESS=true

echo -e "\n${C_GREEN}${C_BOLD}======================================================${C_RESET}"
echo -e "${C_GREEN}${C_BOLD}      🎉 Should-i-Update installed successfully!     ${C_RESET}"
echo -e "${C_GREEN}${C_BOLD}======================================================${C_RESET}"
echo -e "\nRun it anytime by typing:  ${C_CYAN}${C_BOLD}should-i-update${C_RESET}"
echo -e "Reconfigure settings with:  ${C_CYAN}${C_BOLD}should-i-update --configure${C_RESET}"
echo -e "Reset / Replace API key:    ${C_CYAN}${C_BOLD}should-i-update --replace-key${C_RESET}\n"
