# AIChat

English | [Русский](README.ru.md)

Chat app for OpenRouter.ai written in Python (Flet). Builds into an
Android APK right on GitHub Actions - no local Android SDK, JDK, or macOS
required.

## Features

- Chat with 200+ OpenRouter models (including free `:free` models)
- 4-digit PIN login: on first launch you enter your OpenRouter key, the app
  checks the balance and generates a PIN. The key and PIN hash are stored
  in SQLite
- "Reset key" button on the login screen
- Automatic Telegram notification on low balance (24-hour anti-spam)
- Chat history in SQLite, JSON export
- Analytics: tokens, messages per minute, per-model stats

## Installing the APK

1. Open the [Actions](../../actions) tab of this repository
2. Pick the latest **Build APK** run and download the `aichat-apk` artifact
3. Unzip it and install the APK on an Android device (Android 7.0 / SDK 24+,
   the minimum supported by Flutter and its plugins)
4. Allow installing from unknown sources on first launch

## Setup before building

The APK is built with the Telegram bot token. The token lives in GitHub
Secrets and never appears in the source code:

1. Create a bot with [@BotFather](https://t.me/BotFather) via `/newbot` and
   copy the token
2. In the repo: Settings - Secrets and variables - Actions - New repository
   secret
3. Secret name: `TELEGRAM_BOT_TOKEN`, value: the bot token
4. Run the workflow manually (Actions - Build APK - Run workflow) or push

To receive notifications, send `/start` to your bot.

Balance checks require an OpenRouter key. A PIN is generated for any valid
key. With a zero or negative balance the login is allowed with a warning -
the chat works on free `:free` models, and the low balance is tracked by
Telegram notifications.

## Proxy

If openrouter.ai is unreachable from the device directly (ISP/region
blocking, emulator network) - the login screen has an optional "Proxy"
field:

- Format: `http://host:port`, `http://user:pass@host:port` or
  `socks5://host:port`
- The proxy applies to all OpenRouter requests (key check, chat, balance)
- The value is stored in SQLite and pre-filled on next logins,
  including PIN login

Key validation errors are distinguished by cause: "Key not found or
invalid" (API responded 401/403) or "No connection to openrouter.ai" with
details - no internet, blocking, or unreachable proxy.

## Project structure

```
├── src/
│   ├── api/
│   │   └── openrouter.py      - OpenRouter API client + key validation
│   ├── ui/
│   │   ├── components.py      - MessageBubble, ModelSelector, LoginView (PIN)
│   │   └── styles.py          - app styles
│   ├── utils/
│   │   ├── analytics.py       - usage statistics
│   │   ├── cache.py           - SQLite: chat history + auth table (PIN, key)
│   │   ├── logger.py          - file logging
│   │   ├── monitor.py         - resource monitoring (stub on Android)
│   │   ├── notifications.py   - Telegram low-balance notifications
│   │   └── paths.py           - cross-platform app paths
│   ├── assets/icon.png        - app icon
│   └── main.py                - entry point, login window, chat
├── .github/workflows/
│   └── build-apk.yml          - GitHub Actions: flet build apk
├── pyproject.toml             - Flet build config (permissions, version)
├── requirements.txt           - Python dependencies
└── README.md
```

## How the mobile adaptation works

- All paths (SQLite, logs, exports) are resolved from the app data directory,
  not the working directory - on Android the working directory is read-only
- `os.startfile` is only called on Windows
- The Telegram token is baked into the APK at build time from GitHub Secrets;
  chat_id is detected automatically via the Telegram Bot API (`getUpdates`)

## Local build (optional)

```bash
pip install flet==0.86.5
flet build apk --project-name "AIChat" --org "com.example" \
  --bundle-id "com.example.aichat"
```

The Flet CLI installs JDK 17 and the Android SDK automatically on first run.
The `TELEGRAM_BOT_TOKEN` environment variable must be set before building.

## License

[MIT](LICENSE)
