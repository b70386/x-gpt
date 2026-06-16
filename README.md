# ⚡ X-GPT CLI - Multi Provider AI Wrapper

> **A transparent, ethical, and professionally engineered command-line interface for multi-provider AI access.**  
> *No fake hacker aesthetics. No hidden telemetry. Just clean code and honest utility.*

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-yellow.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)
![Providers](https://img.shields.io/badge/Providers-OpenRouter%20|%20DeepSeek%20|%20OpenAI%20|%20Groq-purple)

## 🎯 Philosophy & Transparency Statement

This project was born out of frustration with the current state of "AI wrapper" repositories on GitHub. Many tools in this space rely on misleading branding ("uncensored private models"), poor coding practices and opaque data handling to funnel users toward paid services or Telegram channels.

**X-GPT is a deliberate rejection of that culture.** 

We believe that:
-   **Honesty > Hype:** This is a cloud API wrapper. It uses public APIs (OpenRouter, DeepSeek, etc.). There is no secret model training, no private infrastructure, and no magic. We state this clearly because respecting user intelligence is foundational to ethical software development.
-   **Clean Code > Script Kiddie Tactics:** Dependencies are managed via `requirements.txt`, not auto-installed at runtime. Configuration is explicit, type-hinted where possible, and free of dead code. 
-   **Security by Design:** API keys are stored securely via `.env` files. We provide robust `.gitignore` templates and never hardcode secrets. What you see in the source is exactly what runs on your machine.
-   **Utility Over Aesthetics:** The gradient banner and typing animation exist solely as optional UI polish—not as a smokescreen for lack of functionality. Every feature serves a practical purpose for developers and power users.
-   **Ethical Error Handling:** We respect provider infrastructure. Instead of aggressive auto-scanning, we implement deterministic fallback chains and honor `Retry-After` headers during rate limiting events.

If you're looking for a tool that respects your time, intelligence, and security, you've found it. If you want a "hacker aesthetic" scam, look elsewhere.

---

## ✨ Core Features

### 🧠 Intelligent Provider Routing Engine
X-GPT implements a deterministic routing system based on model ID patterns—no guesswork, no manual URL configuration:

| Model Pattern | Provider | Base URL |
| :--- | :--- | :--- |
| `deepseek-chat`, `deepseek-reasoner` | DeepSeek Official | `api.deepseek.com` |
| `gpt-*`, `o1-*`, `o3-*` | OpenAI | `api.openai.com/v1` |
| `llama-*groq*` | Groq | `api.groq.com/openai/v1` |
| `*/model:free`, `provider/model` | OpenRouter | `openrouter.ai/api/v1` |
| `*/model:flash`, `provider/model` | OpenRouter | `openrouter.ai/api/v1` |
| Custom endpoint | User-defined | Configurable |

The routing logic is fully documented in `resolve_provider()` with explicit rules—no black-box behavior.

### 🔑 Secure Multi-Key Management via .env
-   **Environment Variable Priority:** API keys are loaded from `.env` first, keeping them completely separate from persistent JSON configuration.
-   **Safe Persistence:** Only non-sensitive preferences (models, language, URLs) are saved to `xgpt_config.json`.
-   **Masked Display:** Keys shown in UI are masked (first 8 + last 4 chars only).
-   **Legacy Migration:** Automatically migrates old single-key JSON structures to the new secure format.

### 🛡️ Ethical Rate Limit Handling
When facing 429 (Too Many Requests) errors on free-tier models:
1.  **Respects `Retry-After` Headers:** Waits exactly as long as the provider requests before retrying.
2.  **Static Fallback Chain:** Automatically switches to pre-configured stable alternatives (e.g., DeepSeek Free → Llama 3.3 Free) without aggressive scanning.
3.  **Transparent Feedback:** Clearly informs users when primary models are limited and when fallbacks are activated.
4.  **Capped Retries:** Prevents infinite loops and respects server resources with maximum retry limits.

### 💾 Automatic Chat History Persistence
Never lose your coding sessions or important AI insights again. X-GPT automatically saves every interaction to a structured `chat_history.json` file in array format.

-   **Zero Configuration:** Saving is enabled by default; no extra setup required.
-   **Structured Data:** Each entry includes timestamp, active model, user query, and full AI response for easy parsing or future RAG integration.
-   **Safe Exit Handling:** History is atomically written when you type `exit`, return to `menu`, or press `Ctrl+C`, preventing data loss during interruptions.
-   **Privacy First:** The history file is strictly local and excluded from Git via `.gitignore`. Your conversations never leave your machine unless you explicitly share them.

> 💡 **Tip:** Use the saved JSON array to build personal knowledge bases, analyze your most frequent queries, or feed context back into future sessions programmatically.

### 🎨 Professional Terminal Experience
-   Gradient ASCII banner via Pyfiglet (optional dependency)
-   Typing animation with configurable delay
-   Language auto-detection (English, Indonesian)
-   Persistent saved models list with `/models` slash command
-   Clean error messages with actionable guidance

### 🌍 Bilingual Support (English & Indonesian)

X-GPT is built for a global community. The entire terminal interface—including menus, prompts, error messages, and system notifications—supports seamless switching between **English** and **Indonesian**. 
This isn't just a translation layer; it's a core feature designed to make AI access more inclusive and comfortable for native speakers of both languages. You can switch languages instantly from the main menu without restarting the application.


### 🎥 See It In Action
Watch how X-GPT handles bilingual queries and model switching in real-time:

👉 **[Watch the Full Demo on YouTube](https://www.youtube.com/watch?v=01ksjiA4tuE)**


---

## ⚙️ Installation & Setup

### Prerequisites
-   Python 3.8+
-   Windows / Linux / macOS
-   Active internet connection

### Quick Start
```bash
# Clone repository
git clone https://github.com/b70386/x-gpt.git
cd x-gpt

# Install dependencies properly (no runtime pip install!)
pip install -r requirements.txt

# Create environment file for API keys
cp .env.example .env
# Edit .env with your actual API keys

### First-Time Configuration

1.  Select **Option 3** → Add API keys for desired providers
2.  Select **Option 2** → Choose or add a model ID
3.  Select **Option 4** → Start chatting

> 💡 **Tip:** Use `/models` inside chat to switch between saved models without returning to the main menu.

---

### 📂 Project Structure

| File/Folder | Description |
| :--- | :--- |
| `xgpt.py` | Main application engine (clean, documented, typed) |
| `xgpt_config.json` | Local config for models & preferences (**NEVER COMMIT**) |
| `prompt.md` | Customizable system prompt |
| `chainsaw.txt` | Optional ASCII art asset |
| `requirements.txt` | Pinned dependencies |
| `.gitignore` | Security-first ignore rules |
| `README.md` | You are here |

---

### 🛡️ Security & Ethics Notice

> ⚠️ **CRITICAL TRANSPARENCY DISCLOSURE:**
> -   API keys are stored in **plain text** in `xgpt_config.json`. This is an intentional design choice for local-only tools, but it comes with responsibility.
> -   **NEVER** commit this file to any repository (public or private).
> -   Always verify `.gitignore` excludes `xgpt_config.json` before pushing.
> -   Rotate keys immediately if accidental exposure occurs.
> -   This tool makes **zero** network requests except to the AI provider APIs you configure. No analytics, no telemetry, no third-party callbacks.
> -   The "jailbreak" prompt in `prompt.md` is a simple text file you control entirely. X-GPT does not inject hidden instructions.
>
> We disclose these limitations openly because **trust is earned through transparency, not marketing**.

---

### 🤝 Contributing

Contributions are welcome—but only if they align with our philosophy:

-   ✅ **DO:** Improve code quality, add documentation, fix bugs, suggest cleaner architectures
-   ❌ **DON'T:** Add fake features, obfuscate code, hardcode secrets, or use misleading branding

All PRs must pass basic linting and include updated documentation. We review for **engineering integrity first**, features second.

---

### 📜 License

MIT License — See [LICENSE](LICENSE) for full terms.

This license grants you freedom to use, modify, and distribute X-GPT—with the expectation that you uphold the same standards of honesty and transparency we do.

---

*Built with integrity by b70386. No Telegram funnels. No fake claims. Just good software.*