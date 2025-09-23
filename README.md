# Clipboard-AI

A Windows desktop app that uses your clipboard as a data bus to send text to Groq AI and types the response with human-like cadence.

## Installation

1. Run `ClipboardAI-Setup.exe` to install the app to `C:\Program Files\ClipboardAI`.
2. The installer will create shortcuts and copy default config files to `%APPDATA%\ClipboardAI` if they don't exist.

## Configuration

### API Key
Set your Groq API key in `%APPDATA%\ClipboardAI\.env`:

```
GROQ_API_KEY=your_api_key_here
```

Or use `API_KEY` instead.

### Settings
Edit `%APPDATA%\ClipboardAI\config.toml` to customize hotkeys, typewriter settings, etc.

## Hotkeys

- **Send (Ctrl+Alt+Enter)**: Reads clipboard, sends to AI, types response.
- **Cancel (Ctrl+Alt+Backspace)**: Stops typing immediately.
- **List Models (Ctrl+Alt+F8)**: Fetches and displays available models, copies to clipboard.
- **Diagnostics (Ctrl+Alt+F9)**: Runs health checks, copies report to clipboard.
- **Default Template (Ctrl+Alt+1)**: Switches to default prompt template.
- **Translate Template (Ctrl+Alt+2)**: Switches to Spanish translation template.

## Permissions

The app simulates keystrokes, so Windows may prompt for keyboard permissions. Allow it for the app to work.

## Troubleshooting

- Ensure your API key is valid.
- Check `%APPDATA%\ClipboardAI\logs.txt` if running with `--noconsole`.
- Run diagnostics (Ctrl+Alt+F9) to verify connectivity.
