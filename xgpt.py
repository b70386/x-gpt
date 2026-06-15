#!/usr/bin/env python3
"""
X-GPT CLI - Multi Provider AI Wrapper
=====================================
A professional, transparent, and ethical command-line interface for interacting 
with multiple AI providers through a unified OpenAI-compatible API.

Features:
- Smart provider routing based on model ID patterns
- Secure multi-key management via .env (no hardcoded secrets)
- Clean terminal UI with gradient ASCII banner
- Persistent local configuration for models & preferences
- Static Fallback Chain for rate-limited free tier models
- Respect for Retry-After headers (OpenRouter standard)

Author: b70386
License: MIT
Repository: https://github.com/b70386/x-gpt
"""

import sys
import os
import platform
import time
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables immediately
load_dotenv()

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

CONFIG_FILE = "xgpt_config.json"
PROMPT_FILE = "prompt.md"
SITE_URL = "https://github.com/b70386/x-gpt"
SITE_NAME = "X-GPT CLI"
SUPPORTED_LANGUAGES = ["English", "Indonesian"]

# Default values (only used if config file doesn't exist yet)
DEFAULT_MODEL = os.getenv("XGPT_DEFAULT_MODEL", "qwen/qwen3-coder:free")
DEFAULT_LANGUAGE = os.getenv("XGPT_LANGUAGE", "English")

# Static Fallback Chain for Free Tier Models (Ordered by stability)
# If primary model fails with 429/503, X-GPT will try these in order.
FALLBACK_CHAIN = [
    "qwen/qwen3-coder:free",
    "deepseek/deepseek-chat:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free"
]

# Provider Registry: Centralized definition of supported AI providers
PROVIDER_REGISTRY = {
    "1": {
        "name": "OpenRouter",
        "key": "openrouter",
        "base_url": "https://openrouter.ai/api/v1",
        "prefix": "sk-or-v1-",
        "hint": "Get free keys at openrouter.ai/keys"
    },
    "2": {
        "name": "DeepSeek",
        "key": "deepseek",
        "base_url": "https://api.deepseek.com",
        "prefix": "sk-",
        "hint": "Get keys at platform.deepseek.com/api_keys"
    },
    "3": {
        "name": "OpenAI",
        "key": "openai",
        "base_url": "https://api.openai.com/v1",
        "prefix": "sk-",
        "hint": "Get keys at platform.openai.com/api-keys"
    },
    "4": {
        "name": "Groq",
        "key": "groq",
        "base_url": "https://api.groq.com/openai/v1",
        "prefix": "gsk_",
        "hint": "Get free keys at console.groq.com/keys"
    },
    "5": {
        "name": "Custom Provider",
        "key": None,
        "base_url": None,
        "prefix": "",
        "hint": "Enter any OpenAI-compatible API endpoint"
    }
}


# ============================================================================
# TERMINAL STYLING
# ============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    WHITE = "\033[0;37m"
    BRIGHT_BLACK = "\033[1;30m"
    BRIGHT_RED = "\033[1;31m"
    BRIGHT_GREEN = "\033[1;32m"
    BRIGHT_YELLOW = "\033[1;33m"
    BRIGHT_BLUE = "\033[1;34m"
    BRIGHT_PURPLE = "\033[1;35m"
    BRIGHT_CYAN = "\033[1;36m"
    BRIGHT_WHITE = "\033[1;37m"
    BRIGHT_ORANGE = "\033[38;2;255;165;0m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def typing_print(text: str, delay: float = 0.02) -> None:
    """Simulate typewriter effect for AI responses."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def clear_screen() -> None:
    """Clear terminal screen based on OS."""
    os.system("cls" if platform.system() == "Windows" else "clear")


def mask_key(key: str) -> str:
    """Mask API key for safe display (show first 8 + last 4 chars)."""
    if not key:
        return f"{Colors.GREEN}Not set{Colors.RESET}"
    if len(key) > 12:
        return f"{Colors.GREEN}{key[:8]}...{key[-4:]}{Colors.RESET}"
    return f"{Colors.GREEN}{'*' * len(key)}{Colors.RESET}"


# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

def save_config(config: dict) -> None:
    """Persist non-sensitive configuration to JSON file."""
    # Never save API keys to config file if they came from .env
    safe_config = {k: v for k, v in config.items() if k != "api_keys"}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(safe_config, f, indent=2)


def load_config() -> dict:
    """Load config: JSON takes precedence for user preferences."""
    
    # Start with defaults (only fallback)
    saved_models = [DEFAULT_MODEL]
    language = DEFAULT_LANGUAGE
    provider_urls = {}
    model = DEFAULT_MODEL
    
    # Load persistent preferences from JSON (THIS TAKES PRECEDENCE)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            # User's saved preferences override defaults
            if "saved_models" in loaded and loaded["saved_models"]:
                saved_models = loaded["saved_models"]
            if "language" in loaded:
                language = loaded["language"]
            if "model" in loaded and loaded["model"]:
                model = loaded["model"]  # <-- CRITICAL FIX: Use JSON value
            if "provider_urls" in loaded:
                provider_urls = loaded["provider_urls"]
            
            # Legacy migration
            if "api_key" in loaded and loaded["api_key"]:
                old_url = loaded.get("base_url", "https://openrouter.ai/api/v1")
                target = "custom"
                if "openrouter" in old_url: target = "openrouter"
                elif "deepseek" in old_url: target = "deepseek"
                loaded.setdefault("api_keys", {})[target] = loaded["api_key"]
                del loaded["api_key"]
            if "base_url" in loaded:
                del loaded["base_url"]
        except Exception:
            pass

    # .env ONLY for API keys (never for model/language preferences)
    api_keys = {}
    env_mappings = {
        "openrouter": "XGPT_OPENROUTER_KEY",
        "deepseek": "XGPT_DEEPSEEK_KEY",
        "openai": "XGPT_OPENAI_KEY",
        "groq": "XGPT_GROQ_KEY"
    }
    
    url_map = {
        "openrouter": "https://openrouter.ai/api/v1",
        "deepseek": "https://api.deepseek.com",
        "openai": "https://api.openai.com/v1",
        "groq": "https://api.groq.com/openai/v1"
    }
    
    for provider, env_var in env_mappings.items():
        key = os.getenv(env_var)
        if key:
            api_keys[provider] = key
            if provider not in provider_urls:
                provider_urls[provider] = url_map[provider]

    return {
        "api_keys": api_keys,
        "provider_urls": provider_urls,
        "model": model,          # <-- Now correctly uses JSON value
        "language": language,     # <-- Now correctly uses JSON value
        "saved_models": saved_models
    }


# ============================================================================
# UI COMPONENTS
# ============================================================================

def banner() -> None:
    """Display the X-GPT branded banner with gradient ASCII art."""
    try:
        import pyfiglet
        figlet = pyfiglet.Figlet(font="big")
        art = figlet.renderText('X-GPT')
        lines = art.split('\n')
        mid = len(lines) // 2

        for i, line in enumerate(lines):
            if not line.strip():
                print(line)
            elif i < mid:
                print(f"{Colors.BRIGHT_GREEN}{line}{Colors.RESET}")
            else:
                print(f"{Colors.BRIGHT_ORANGE}{line}{Colors.RESET}")
    except ImportError:
        print(f"{Colors.BRIGHT_GREEN}X-GPT{Colors.BRIGHT_ORANGE}>{Colors.RESET}")

    print(f"{Colors.BRIGHT_ORANGE}X-GPT CLI - Multi Provider Edition & Cloud AI Wrapper{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}OpenRouter | DeepSeek | OpenAI | Groq | Custom{Colors.RESET}")
    print(f"{Colors.BRIGHT_CYAN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")


def get_system_prompt() -> str:
    """Load system prompt from file or create default."""
    default_prompt = "You are X-GPT, an AI assistant."

    if not os.path.exists(PROMPT_FILE):
        try:
            with open(PROMPT_FILE, "w", encoding="utf-8") as f:
                f.write(default_prompt)
        except Exception:
            pass
        return default_prompt

    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return content if content else default_prompt
    except Exception as e:
        print(f"{Colors.RED}Warning: Could not read {PROMPT_FILE}: {e}{Colors.RESET}")
        return default_prompt


# ============================================================================
# SMART ROUTING ENGINE
# ============================================================================

def resolve_provider(model: str) -> tuple:
    """
    Automatically determine the correct provider, URL, and API key
    based on the model ID string.

    Returns: (provider_key, base_url, api_key) or (None, None, None)
    """
    config = load_config()
    api_keys = config.get("api_keys", {})
    provider_urls = config.get("provider_urls", {})

    # Rule 1: DeepSeek official models
    if model in ("deepseek-chat", "deepseek-reasoner", "deepseek-chat-v3", "deepseek-r1"):
        if api_keys.get("deepseek"):
            return ("deepseek",
                    provider_urls.get("deepseek", "https://api.deepseek.com"),
                    api_keys["deepseek"])

    # Rule 2: OpenAI official models
    if model.startswith(("gpt-", "o1-", "o3-")):
        if api_keys.get("openai"):
            return ("openai",
                    provider_urls.get("openai", "https://api.openai.com/v1"),
                    api_keys["openai"])

    # Rule 3: Groq models
    if model.startswith("llama-") and "groq" in model:
        if api_keys.get("groq"):
            return ("groq",
                    provider_urls.get("groq", "https://api.groq.com/openai/v1"),
                    api_keys["groq"])

    # Rule 4: OpenRouter models (contains '/' or ':free')
    if "/" in model or ":free" in model:
        if api_keys.get("openrouter"):
            return ("openrouter",
                    provider_urls.get("openrouter", "https://openrouter.ai/api/v1"),
                    api_keys["openrouter"])

    # Rule 5: Fallback - use first available configured provider
    for provider_key, key_value in api_keys.items():
        if key_value:
            url = provider_urls.get(provider_key, "")
            for info in PROVIDER_REGISTRY.values():
                if info["key"] == provider_key and info["base_url"]:
                    return (provider_key, info["base_url"], key_value)
            if url:
                return (provider_key, url, key_value)

    return (None, None, None)


# ============================================================================
# API COMMUNICATION WITH FALLBACK & RETRY-AFTER
# ============================================================================

def call_api(user_input: str, retry_count: int = 0, fallback_index: int = 0) -> str:
    """
    Send chat request with intelligent error handling:
    1. Respects Retry-After header for 429/503 errors.
    2. Uses Static Fallback Chain if primary model is rate-limited.
    3. Limits retries to prevent infinite loops.
    """
    config = load_config()
    
    # Determine current model to use
    if fallback_index == 0:
        model = config["model"]
    else:
        # Use model from fallback chain
        if fallback_index < len(FALLBACK_CHAIN):
            model = FALLBACK_CHAIN[fallback_index]
        else:
            return f"{Colors.RED}[X-GPT] All fallback models exhausted. Please try again later.{Colors.RESET}"

    # Resolve provider for the current model
    provider_key, base_url, api_key = resolve_provider(model)

    if not provider_key:
        if fallback_index == 0:
            return (f"{Colors.RED}[X-GPT] Error: No API key configured for model '{model}'.\n"
                    f"Please go to Menu 3 (Set API Key) and add a key for the appropriate provider.{Colors.RESET}")
        else:
            # If fallback model has no key, try next fallback
            return call_api(user_input, retry_count, fallback_index + 1)

    # Build request payload
    clean_url = base_url.strip().rstrip('/')
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # OpenRouter requires attribution headers
    if provider_key == "openrouter":
        headers["HTTP-Referer"] = SITE_URL
        headers["X-Title"] = SITE_NAME

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": get_system_prompt()},
            {"role": "user", "content": user_input}
        ],
        "max_tokens": 2000,
        "temperature": 0.7
    }

    # Display routing info (only show on first attempt or when switching fallbacks)
    if retry_count == 0 and fallback_index == 0:
        print(f"{Colors.BRIGHT_BLACK}  → Routing: {provider_key.upper()} | {clean_url}{Colors.RESET}")
    elif fallback_index > 0:
        print(f"{Colors.YELLOW}  → Fallback {fallback_index}: Using {model} via {provider_key.upper()}{Colors.RESET}")

    try:
        response = requests.post(
            f"{clean_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=120
        )
        
        # Check for empty response
        if response.status_code == 200:
            try:
                content = response.json()['choices'][0]['message']['content']
                if not content or content.strip() == "":
                    raise Exception("Empty content from model")
                return content
            except (KeyError, IndexError, Exception) as e:
                if retry_count < 2:
                    print(f"{Colors.YELLOW}[X-GPT] Empty response. Retrying...{Colors.RESET}")
                    time.sleep(2)
                    return call_api(user_input, retry_count + 1, fallback_index)
                return f"{Colors.RED}[X-GPT] Model returned empty response after retries.{Colors.RESET}"

        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']

    except requests.exceptions.HTTPError as e:
        status_code = response.status_code
        
        # Handle Rate Limiting (429) & Service Unavailable (503) per OpenRouter docs
        if status_code in (429, 503):
            # Respect Retry-After header
            retry_after = response.headers.get("Retry-After")
            wait_time = int(retry_after) if retry_after and retry_after.isdigit() else 10
            
            # Cap wait time to 60 seconds max
            wait_time = min(wait_time, 60)
            
            if retry_count < 2:
                print(f"{Colors.YELLOW}[X-GPT] Rate limited ({status_code}). Waiting {wait_time}s (per Retry-After)...{Colors.RESET}")
                time.sleep(wait_time)
                return call_api(user_input, retry_count + 1, fallback_index)
            else:
                # After retries exhausted, try fallback chain
                if fallback_index < len(FALLBACK_CHAIN) - 1:
                    print(f"{Colors.YELLOW}[X-GPT] Primary model still limited. Switching to fallback...{Colors.RESET}")
                    return call_api(user_input, 0, fallback_index + 1)
                else:
                    return f"{Colors.RED}[X-GPT] All models currently rate limited. Please try again in a few minutes.{Colors.RESET}"
        
        # Handle other HTTP errors
        error_body = response.text[:200] if response else str(e)
        
        # Specific error messages
        if status_code == 401:
            return f"{Colors.RED}[X-GPT] Invalid API Key for {provider_key}. Please update it in Menu 3.{Colors.RESET}"
        elif status_code == 402:
            return f"{Colors.RED}[X-GPT] Insufficient credits for {provider_key}.{Colors.RESET}"
        elif status_code == 403:
            return f"{Colors.RED}[X-GPT] Request blocked by guardrails/moderation.{Colors.RESET}"
        elif status_code == 404:
            return f"{Colors.RED}[X-GPT] Model '{model}' not found. Please check the model ID.{Colors.RESET}"
        
        return (f"{Colors.RED}[X-GPT] HTTP {status_code} ({provider_key}): "
                f"{error_body}{Colors.RESET}")
                
    except requests.exceptions.Timeout:
        if retry_count < 2:
            print(f"{Colors.YELLOW}[X-GPT] Request timed out. Retrying...{Colors.RESET}")
            time.sleep(3)
            return call_api(user_input, retry_count + 1, fallback_index)
        return f"{Colors.RED}[X-GPT] Request timeout after multiple attempts.{Colors.RESET}"
        
    except Exception as e:
        return f"{Colors.RED}[X-GPT] Error: {str(e)}{Colors.RESET}"


# ============================================================================
# MENU SYSTEM
# ============================================================================

def select_language() -> None:
    """Interactive language selection menu."""
    config = load_config()
    clear_screen()
    banner()

    print(f"\n{Colors.BRIGHT_CYAN}[ Language Selection ]{Colors.RESET}")
    print(f"{Colors.YELLOW}Current: {Colors.GREEN}{config['language']}{Colors.RESET}\n")

    for idx, lang in enumerate(SUPPORTED_LANGUAGES, 1):
        print(f"{Colors.GREEN}{idx}. {lang}{Colors.RESET}")

    while True:
        try:
            choice = int(input(f"\n{Colors.GREEN}[>] Select (1-{len(SUPPORTED_LANGUAGES)}): {Colors.RESET}"))
            if 1 <= choice <= len(SUPPORTED_LANGUAGES):
                config["language"] = SUPPORTED_LANGUAGES[choice - 1]
                save_config(config)
                print(f"{Colors.BRIGHT_CYAN}Language set to {SUPPORTED_LANGUAGES[choice - 1]}{Colors.RESET}")
                time.sleep(1)
                return
            print(f"{Colors.RED}Invalid selection!{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}Please enter a number{Colors.RESET}")


def select_model() -> None:
    """Interactive model configuration with saved models list."""
    config = load_config()
    clear_screen()
    banner()

    print(f"\n{Colors.BRIGHT_CYAN}[ Model Configuration ]{Colors.RESET}")
    print(f"{Colors.YELLOW}Current Active: {Colors.GREEN}{config['model']}{Colors.RESET}\n")
    print(f"{Colors.YELLOW}1. Enter new custom model ID{Colors.RESET}")
    print(f"{Colors.YELLOW}2. Switch from Saved Models list{Colors.RESET}")
    print(f"{Colors.YELLOW}3. Back to menu{Colors.RESET}")

    while True:
        choice = input(f"\n{Colors.GREEN}[>] Select (1-3): {Colors.RESET}").strip()

        if choice == "1":
            new_model = input(f"{Colors.GREEN}Enter model ID: {Colors.RESET}").strip()
            if new_model:
                config["model"] = new_model
                if new_model not in config["saved_models"]:
                    config["saved_models"].append(new_model)
                save_config(config)
                print(f"{Colors.BRIGHT_CYAN}Model updated and saved!{Colors.RESET}")
                time.sleep(1)
                return

        elif choice == "2":
            # Reload fresh config before displaying
            config = load_config() 
            
            if not config.get("saved_models"):
                print(f"{Colors.RED}No saved models yet!{Colors.RESET}")
                time.sleep(1)
                continue

            print(f"\n{Colors.BRIGHT_CYAN}Available Models:{Colors.RESET}")
            for i, m in enumerate(config["saved_models"], 1):
                marker = " [ACTIVE]" if m == config["model"] else ""
                print(f"{Colors.GREEN}{i}. {m}{Colors.YELLOW}{marker}{Colors.RESET}")

            sel = input(f"\n{Colors.GREEN}Enter number to switch (or 0 to cancel): {Colors.RESET}").strip()
            try:
                idx = int(sel)
                if 1 <= idx <= len(config["saved_models"]):
                    selected = config["saved_models"][idx - 1]
                    
                    # Direct update + Save
                    config["model"] = selected
                    save_config(config)
                    
                    # Verification step
                    verified = load_config()
                    if verified["model"] == selected:
                        pk, bu, _ = resolve_provider(selected)
                        print(f"{Colors.BRIGHT_CYAN}Switched to {selected}{Colors.RESET}")
                        print(f"{Colors.BRIGHT_BLACK}  → Provider: {pk.upper() if pk else 'NONE'} | {bu}{Colors.RESET}")
                    else:
                        print(f"{Colors.RED}Failed to persist. Retrying...{Colors.RESET}")
                        save_config(config)  # Retry once
                        time.sleep(1)
                        
                    time.sleep(2)
                    return
            except ValueError:
                pass

        elif choice == "3":
            return
        else:
            print(f"{Colors.RED}Invalid choice!{Colors.RESET}")


def set_api_key() -> None:
    """Multi-provider API key management interface."""
    config = load_config()
    clear_screen()
    banner()

    print(f"\n{Colors.BRIGHT_CYAN}[ Multi-Provider API Key Configuration ]{Colors.RESET}")
    print(f"{Colors.BRIGHT_YELLOW}Manage API keys for different AI providers{Colors.RESET}\n")

    # Initialize dicts if missing
    config.setdefault("api_keys", {})
    config.setdefault("provider_urls", {})

    # Display current keys status
    print(f"{Colors.YELLOW}━━━ Current API Keys ━━━{Colors.RESET}")
    for num, info in PROVIDER_REGISTRY.items():
        if info["key"]:
            key = config["api_keys"].get(info["key"], "")
            status = mask_key(key) if key else f"{Colors.GREEN}Not set{Colors.RESET}"
            print(f"  {Colors.WHITE}{num}. {info['name']:15s}{Colors.RESET} : {status}")
        else:
            custom_keys = [k for k in config["api_keys"]
                           if k not in [v["key"] for v in PROVIDER_REGISTRY.values() if v["key"]]]
            if custom_keys:
                for ck in custom_keys:
                    key = config["api_keys"].get(ck, "")
                    status = mask_key(key) if key else f"{Colors.GREEN}Not set{Colors.RESET}"
                    print(f"  {Colors.WHITE}   {ck.capitalize():15s}{Colors.RESET} : {status}")
            else:
                print(f"  {Colors.WHITE}{num}. Custom Provider{Colors.RESET}    : {Colors.CYAN}Add new{Colors.RESET}")

    print(f"\n  {Colors.WHITE}6. Delete a stored key{Colors.RESET}")
    print(f"  {Colors.WHITE}7. Back to menu{Colors.RESET}")

    while True:
        choice = input(f"\n{Colors.GREEN}[>] Select option (1-7): {Colors.RESET}").strip()

        if choice == "7":
            return

        if choice == "6":
            if not config["api_keys"]:
                print(f"{Colors.RED}No keys stored to delete!{Colors.RESET}")
                time.sleep(1)
                return set_api_key()

            print(f"\n{Colors.YELLOW}Keys to delete:{Colors.RESET}")
            keys_list = list(config["api_keys"].keys())
            for i, k in enumerate(keys_list, 1):
                print(f"  {Colors.GREEN}{i}. {k.capitalize()}{Colors.RESET}")

            sel = input(f"\n{Colors.GREEN}Enter number to delete (or 0 to cancel): {Colors.RESET}").strip()
            try:
                idx = int(sel)
                if 1 <= idx <= len(keys_list):
                    deleted_key = keys_list[idx - 1]
                    del config["api_keys"][deleted_key]
                    config["provider_urls"].pop(deleted_key, None)
                    save_config(config)
                    print(f"{Colors.BRIGHT_CYAN}Key for '{deleted_key}' deleted!{Colors.RESET}")
                    time.sleep(1)
                    return set_api_key()
            except ValueError:
                pass
            continue

        if choice in PROVIDER_REGISTRY:
            provider_info = PROVIDER_REGISTRY[choice]

            if provider_info["key"] is None:
                # Custom provider flow
                custom_name = input(f"\n{Colors.GREEN}Enter custom provider name (e.g., 'lmstudio'): {Colors.RESET}").strip().lower()
                if not custom_name:
                    print(f"{Colors.RED}Provider name cannot be empty!{Colors.RESET}")
                    continue

                custom_url = input(f"{Colors.GREEN}Enter API Base URL (e.g., http://localhost:1234/v1): {Colors.RESET}").strip()
                if not custom_url:
                    print(f"{Colors.RED}Base URL cannot be empty!{Colors.RESET}")
                    continue

                provider_key = custom_name
                provider_display = custom_name.capitalize()
                provider_url = custom_url.rstrip('/')
            else:
                provider_key = provider_info["key"]
                provider_display = provider_info["name"]
                provider_url = provider_info["base_url"]
                print(f"\n{Colors.BRIGHT_CYAN}ℹ {provider_info['hint']}{Colors.RESET}")

            # Check for existing key
            existing = config["api_keys"].get(provider_key, "")
            if existing:
                print(f"{Colors.YELLOW}Current key: {mask_key(existing)}{Colors.RESET}")
                overwrite = input(f"{Colors.GREEN}Overwrite? (y/n): {Colors.RESET}").strip().lower()
                if overwrite != 'y':
                    continue

            new_key = input(f"\n{Colors.GREEN}Enter {provider_display} API key: {Colors.RESET}").strip()
            if new_key:
                config["api_keys"][provider_key] = new_key
                config["provider_urls"][provider_key] = provider_url
                save_config(config)
                print(f"\n{Colors.BRIGHT_GREEN}✓ {provider_display} API key saved successfully!{Colors.RESET}")
                print(f"{Colors.BRIGHT_CYAN}  Base URL: {provider_url}{Colors.RESET}")
                time.sleep(2)
                return
            else:
                print(f"{Colors.RED}API key cannot be empty!{Colors.RESET}")
        else:
            print(f"{Colors.RED}Invalid choice!{Colors.RESET}")


def chat_session() -> None:
    """Main interactive chat loop with slash commands."""
    config = load_config()
    clear_screen()
    banner()

    provider_key, base_url, _ = resolve_provider(config["model"])
    provider_display = provider_key.upper() if provider_key else "NONE"

    print(f"\n{Colors.BRIGHT_CYAN}[ Chat Session ]{Colors.RESET}")
    print(f"{Colors.YELLOW}Model    : {Colors.GREEN}{config['model']}{Colors.RESET}")
    print(f"{Colors.YELLOW}Provider : {Colors.BRIGHT_GREEN}{provider_display}{Colors.RESET}")
    print(f"{Colors.YELLOW}Commands : {Colors.WHITE}'menu' | '/models' | 'clear' | 'exit'{Colors.RESET}\n")

    while True:
        try:
            user_input = input(f"{Colors.BRIGHT_GREEN}[X-GPT] {Colors.RESET}").strip()

            if not user_input:
                continue

            # Command handlers
            if user_input.lower() == "exit":
                print(f"{Colors.BRIGHT_CYAN}Exiting...{Colors.RESET}")
                sys.exit(0)

            elif user_input.lower() == "menu":
                return

            elif user_input.lower() == "clear":
                clear_screen()
                banner()
                print(f"\n{Colors.BRIGHT_CYAN}[ Chat Session ]{Colors.RESET}")
                continue

            elif user_input.lower() == "/models":
                print(f"\n{Colors.BRIGHT_CYAN}--- Saved Models ---{Colors.RESET}")
                for i, m in enumerate(config["saved_models"], 1):
                    marker = f" {Colors.GREEN}<< ACTIVE{Colors.RESET}" if m == config["model"] else ""
                    print(f"  {Colors.YELLOW}{i}. {m}{marker}{Colors.RESET}")
                print(f"{Colors.BRIGHT_CYAN}--------------------{Colors.RESET}")

                sel = input(f"{Colors.GREEN}Type number to switch (or press Enter to cancel): {Colors.RESET}").strip()
                try:
                    idx = int(sel)
                    if 1 <= idx <= len(config["saved_models"]):
                        config["model"] = config["saved_models"][idx - 1]
                        save_config(config)
                        print(f"{Colors.BRIGHT_CYAN}Switched to {config['model']}{Colors.RESET}")
                        pk, bu, _ = resolve_provider(config["model"])
                        print(f"{Colors.BRIGHT_BLACK}  → Provider: {pk.upper() if pk else 'NONE'} | {bu}{Colors.RESET}")
                except ValueError:
                    pass
                continue

            # Send to API with automatic fallback handling
            response = call_api(user_input)
            if response:
                print(f"\n{Colors.BRIGHT_CYAN}Response:{Colors.RESET}\n{Colors.WHITE}", end="")
                typing_print(response)

        except KeyboardInterrupt:
            print(f"\n{Colors.RED}Interrupted!{Colors.RESET}")
            return
        except Exception as e:
            print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")


def main_menu() -> None:
    """Main application menu loop."""
    while True:
        config = load_config()
        clear_screen()
        banner()

        api_keys = config.get("api_keys", {})
        configured_count = sum(1 for v in api_keys.values() if v)

        print(f"\n{Colors.BRIGHT_CYAN}[ Main Menu ]{Colors.RESET}")
        print(f"{Colors.YELLOW}1. Language  : {Colors.GREEN}{config['language']}{Colors.RESET}")
        print(f"{Colors.YELLOW}2. Model     : {Colors.GREEN}{config['model']}{Colors.RESET}")
        print(f"{Colors.YELLOW}3. API Keys  : {Colors.GREEN}{configured_count} provider(s) configured{Colors.RESET}")
        print(f"{Colors.YELLOW}4. Start Chat{Colors.RESET}")
        print(f"{Colors.YELLOW}5. Exit{Colors.RESET}")

        try:
            choice = input(f"\n{Colors.GREEN}[>] Select (1-5): {Colors.RESET}").strip()

            actions = {
                "1": select_language,
                "2": select_model,
                "3": set_api_key,
                "4": chat_session,
            }

            if choice == "5":
                print(f"{Colors.BRIGHT_CYAN}Exiting...{Colors.RESET}")
                sys.exit(0)
            elif choice in actions:
                actions[choice]()
            else:
                print(f"{Colors.RED}Invalid selection!{Colors.RESET}")
                time.sleep(1)

        except KeyboardInterrupt:
            print(f"\n{Colors.RED}Interrupted!{Colors.RESET}")
            sys.exit(1)
        except Exception as e:
            print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")
            time.sleep(2)


# ============================================================================
# ENTRY POINT
# ============================================================================

def main() -> None:
    """Application entry point with dependency validation."""
    # Validate required dependencies
    try:
        import pyfiglet
    except ImportError:
        print(f"\n{Colors.RED}[ERROR] Missing dependency: pyfiglet{Colors.RESET}")
        print(f"{Colors.YELLOW}Please run: pip install -r requirements.txt{Colors.RESET}\n")
        sys.exit(1)

    try:
        from langdetect import detect  # noqa: F811
    except ImportError:
        print(f"\n{Colors.RED}[ERROR] Missing dependency: langdetect{Colors.RESET}")
        print(f"{Colors.YELLOW}Please run: pip install -r requirements.txt{Colors.RESET}\n")
        sys.exit(1)

    # Initialize config file if it doesn't exist
    if not os.path.exists(CONFIG_FILE):
        save_config(load_config())

    try:
        while True:
            main_menu()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Interrupted! Exiting...{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()