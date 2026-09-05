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

For Telegram notifications the app uses a bridge - a separate service with
two endpoints (`/send` and `/updates`) that proxies requests to the
Telegram Bot API. The bot token lives on the bridge side and never appears
in the APK or the source code:

1. Deploy the bridge and set two environment variables on its side:
   the bot token (`TELEGRAM_BOT_TOKEN`, from
   [@BotFather](https://t.me/BotFather)) and a secret (`BRIDGE_SECRET`)
   to reject foreign requests
2. In the repo: Settings - Secrets and variables - Actions - New
   repository secret - add two secrets:
   - `TELEGRAM_BRIDGE_URL` - the bridge address
   - `TELEGRAM_BRIDGE_SECRET` - the bridge `BRIDGE_SECRET` value
3. Run the workflow manually (Actions - Build APK - Run workflow) or push

## Binding chat_id in the app

After logging in, tap the bell icon next to the Clear button. Two ways
to bind:

- **Confirmation code (recommended):** the app shows a code and copies
  it to the clipboard. Send the code as a message to your bot and tap
  "Verify" - only the account that sent the code gets bound, a foreign
  chat_id cannot bind
- **Manual chat_id:** get your id via `/start` to `@userinfobot` and
  type it in the field

The "Send test" button checks the connection instantly. The low balance
notification (below $0.50) is sent automatically on every app login.

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
- The bridge config (address and secret) is baked into the APK at build time
  from GitHub Secrets; the bot token stays on the bridge side
- Telegram requests go through the bridge - Bot API blocking does not
  affect notifications

## Local build (optional)

```bash
pip install flet==0.86.5
flet build apk --project-name "AIChat" --org "com.example" \
  --bundle-id "com.example.aichat"
```

The Flet CLI installs JDK 17 and the Android SDK automatically on first run.
The `TELEGRAM_BRIDGE_URL` and `TELEGRAM_BRIDGE_SECRET` environment variables
must be set before building.

## License

[MIT](LICENSE)
