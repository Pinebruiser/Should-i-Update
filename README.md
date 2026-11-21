# Should-i-Update

An intelligent package update decision assistant for **Arch Linux** and **CachyOS**.

Instead of blindly running `pacman -Syu`, `Should-i-Update` inspects your pending updates, checks recent Arch Linux news for manual intervention advisories, and categorizes packages into actionable buckets using your choice of LLM.

---

## Highlights

- **4-Bucket Triage:**
  - **`UPNOW`**: Urgent security patches, kernel updates, breaking changes, or manual intervention alerts.
  - **`COOLFEAT`**: Notable major version releases and new user-facing features.
  - **`IFYOUWANT`**: Standard point releases and routine bug fixes safe to defer.
  - **`REDUNDANT`**: Minor rebuilds, documentation, or localization updates with negligible impact.
- **Zero-Plaintext Security:** API keys are stored in the default **Linux Secret Service** (GNOME Keyring / KWallet / KeePassXC) via `secret-tool`. Keys persist across reboots without being exposed in dotfiles.
- **Up-To-Date Knowledge:** Injects recent Arch Linux RSS news and package metadata directly into prompts to eliminate LLM training cutoff issues.
- **Lightweight Engine:** Built purely with Python standard library HTTP (`urllib.request`). No heavy SDKs or virtual environment bloat.
- **AUR Integration:** Optionally checks and categorizes AUR updates using `yay -Qua` or `paru -Qua`.
- **Flexible Providers:** Supports Google Gemini (free tier), OpenRouter (auto-routing & free/paid models), Anthropic Claude, and OpenAI.

---

## Quick Installation

Run the one-line installer:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Pinebruiser/Should-i-Update/main/install.sh)"
```

The installer verifies prerequisites (`pacman-contrib`, `python`, `libsecret`), prompts for your preferred provider, safely configures the Linux Secret Service, and links `should-i-update` to `~/.local/bin/`.

---

## Usage

Simply run:

```bash
should-i-update
```

### Options

| Flag | Description |
| :--- | :--- |
| `--dry-run` | Analyze and categorize packages without prompting to update |
| `--replace-key` | Replace the API key for your current active provider |
| `--reset-key` | Remove current API key from Linux Secret Service with next-step guidance |
| `--change-provider` | Switch to a new provider and store its API key |
| `--configure` | Re-run the full interactive setup wizard |
| `--provider <name>` | Override provider for a single run (`gemini`, `openrouter`, `claude`, `openai`) |
| `--model <model>` | Override the model name for a single run |
| `--timeout <seconds>` | Override request timeout in seconds (default: 180) |
| `--no-aur` | Skip AUR package checks |
| `--aur` | Force AUR package checks |
| `--raw` | Output raw JSON for automation and scripting |
| `--update-cmd <cmd>` | Override the command executed upon confirmation |

---

## Providers & Default Models

| Provider | Default Model | Notes |
| :--- | :--- | :--- |
| **Google Gemini** | `gemini-3.6-flash` | Free tier available via Google AI Studio (recommended default) |
| **OpenRouter** | `openrouter/auto` | Auto-routing across models, free & paid open model support |
| **Anthropic Claude** | `claude-3-5-haiku-20241022` | Cost-effective, high quality reasoning |
| **OpenAI** | `gpt-4o-mini` | Fast and lightweight |

---

## Configuration

Preferences are stored in `~/.config/should-i-update/config.json`. Note that API keys are never stored here.

```json
{
  "provider": "gemini",
  "curr_model": "gemini-3.6-flash",
  "saved_models": {
    "gemini": "gemini-3.6-flash",
    "openrouter": "openrouter/auto"
  },
  "request_timeout": 180,
  "check_aur": true,
  "aur_helper": "yay",
  "update_command": "sudo cachyos-rate-mirrors && yay -Syu",
  "check_arch_news": true
}
```

> **Note:** API requests use a 3-minute (180s) timeout to accommodate large updates (300+ packages) where upstream LLM providers may queue requests or process deep reasoning tokens.

