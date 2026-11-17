import argparse
import json
import sys
from typing import List

from .config import get_default_model, load_config
from .formatter import render_report
from .keychain import get_api_key
from .news import fetch_arch_news, find_news_matches
from .packages import PackageUpdate, parse_package_line, prioritize_packages
from .prompt import SYSTEM_PROMPT, build_user_prompt
from .providers import get_provider


def main() -> int:
    parser = argparse.ArgumentParser(description="Should-i-Update Analysis Engine")
    parser.add_argument("--provider", help="Override LLM provider")
    parser.add_argument("--model", help="Override LLM model name")
    parser.add_argument("--raw", action="store_true", help="Output raw JSON instead of formatted text")
    parser.add_argument("--no-news", action="store_true", help="Disable Arch Linux news check")
    parser.add_argument("--save-json", help="Save the raw JSON result to a specified file path")
    parser.add_argument("input_file", nargs="?", default="-", help="Input file or '-' for stdin")

    args = parser.parse_args()


    config = load_config()
    if args.provider:
        config["provider"] = args.provider
        config["curr_model"] = config["saved_models"].get(
            args.provider.lower(), get_default_model(args.provider.lower())
        )
    if args.model:
        config["curr_model"] = args.model

    provider_name = config.get("provider", "gemini").lower()

  
    if args.input_file == "-":
        lines = sys.stdin.readlines()
    else:
        try:
            with open(args.input_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            sys.stderr.write(f"Error reading package list: {e}\n")
            return 1

    packages: List[PackageUpdate] = []
    for line in lines:
        parsed = parse_package_line(line)
        if parsed:
            packages.append(parsed)

    total_count = len(packages)
    if total_count == 0:
        if args.raw:
            print(json.dumps({"verdict": "UP_TO_DATE", "summary": "System is up to date.", "categories": {}}))
        else:
            print("No pending updates found.")
        return 0

    news_matches = []
    if config.get("check_arch_news", True) and not args.no_news:
        news_items = fetch_arch_news(max_items=6)
        pkg_names = [p.name for p in packages]
        news_matches = find_news_matches(pkg_names, news_items)

    # Prioritize packages for the prompt
    prompt_packages = prioritize_packages(packages)

    # Build prompts
    user_prompt = build_user_prompt(prompt_packages, total_count=total_count, news_items=news_matches)

    # Resolve API Key
    api_key = get_api_key(provider_name) or ""
    if not api_key:
        sys.stderr.write(
            f"\n[!] No API key found for provider '{provider_name}'.\n"
            f"    Please run 'should-i-update --replace-key' to set your API key in the Linux Secret Service,\n"
            f"    or export {provider_name.upper()}_API_KEY='your-key'.\n"
        )
        return 2

    # Instantiate Provider and query
    try:
        provider = get_provider(provider_name, config, api_key=api_key)
        result = provider.query(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
    except Exception as e:
        sys.stderr.write(f"\n[!] Analysis failed: {e}\n")
        return 3

    if args.save_json:
        try:
            with open(args.save_json, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to save JSON to {args.save_json}: {e}\n")

    # Output result
    if args.raw:
        print(json.dumps(result, indent=2))
    else:
        print(render_report(result, total_pkgs=total_count))

    return 0


if __name__ == "__main__":
    sys.exit(main())

