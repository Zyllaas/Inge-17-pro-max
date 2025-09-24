# Clipboard-AI

A Windows desktop application that transforms your clipboard into an AI-powered productivity tool. Send clipboard text to Groq AI and receive responses typed directly into your active application with human-like cadence.

## ✨ Features

- **Global Hotkeys**: Work from any application without switching windows
- **Typewriter Effect**: AI responses are typed naturally with realistic timing
- **Privacy Protection**: Automatically blocks sensitive content (API keys, passwords)
- **Template System**: Switch between different prompt templates
- **Health Diagnostics**: Built-in system to verify API connectivity
- **Portable**: Single executable file, no installation required

## 🚀 Quick Start

### Option 1: Use the Installer
1. Download and run `ClipboardAI-Setup.exe`
2. The installer will place the app in `C:\Program Files\ClipboardAI`
3. Set your API key in `%APPDATA%\ClipboardAI\.env`

### Option 2: Portable Executable
1. Download `ClipboardAI.exe`
2. Create a `.env` file in the same folder with your API key
3. Run the executable

## ⚙️ Configuration

### API Key Setup
Create or edit `%APPDATA%\ClipboardAI\.env`:
```
GROQ_API_KEY=your_groq_api_key_here
MODEL=llama-3.1-8b-instant
API_BASE=https://api.groq.com/openai/v1
```

### Settings
Edit `%APPDATA%\ClipboardAI\config.toml` to customize:
- Hotkey combinations
- Typing speed and behavior
- Privacy patterns
- API timeouts

## 🎮 Default Hotkeys

| Hotkey | Function |
|--------|----------|
| `Ctrl+Alt+Enter` | Send clipboard to AI and type response |
| `Ctrl+Alt+Backspace` | Cancel current typing |
| `Ctrl+Alt+F8` | List available models |
| `Ctrl+Alt+F9` | Run diagnostics |
| `Ctrl+Alt+1` | Switch to default template |
| `Ctrl+Alt+2` | Switch to Spanish translation template |

## 🛡️ Privacy & Security

The app includes built-in privacy protection that automatically blocks requests containing:
- API keys (patterns like `sk-...`)
- Password assignments (`password=...`)
- Authorization tokens (`Authorization: Bearer ...`)

You can customize these patterns in `config.toml`.

## 🔧 Troubleshooting

### Permission Issues
Windows may prompt for keyboard permissions when first running the app. This is normal - the app needs permission to simulate typing.

### API Connection Issues
1. Verify your API key is correct
2. Run diagnostics (`Ctrl+Alt+F9`) to check connectivity
3. Check logs at `%APPDATA%\ClipboardAI\logs.txt` if running with `--noconsole`

### Common Issues
- **Nothing happens when pressing hotkeys**: Check if another app is using the same hotkey combination
- **Typing is too fast/slow**: Adjust `min_cps` and `max_cps` in `config.toml`
- **API errors**: Verify your Groq API key and check rate limits

## 🏗️ Building from Source

### Requirements
- Python 3.11+
- Windows 10/11 x64

### Build Steps
```bash
# Clone the repository
git clone https://github.com/yourusername/clipboard-ai.git
cd clipboard-ai

# Install dependencies
pip install -r requirements.txt

# Build executable
build.bat

# Build installer (requires Inno Setup)
iscc installer.iss
```

## 📁 File Locations

- **Executable**: `dist/ClipboardAI.exe` (after build)
- **User Config**: `%APPDATA%\ClipboardAI\config.toml`
- **Environment**: `%APPDATA%\ClipboardAI\.env`
- **Templates**: `%APPDATA%\ClipboardAI\templates\`
- **Logs**: `%APPDATA%\ClipboardAI\logs.txt`

## 🎯 Usage Examples

### Basic Usage
1. Copy text to clipboard: "Write a professional email asking for a project update"
2. Press `Ctrl+Alt+Enter`
3. Watch as the AI response is typed into your active application

### With Templates
1. Press `Ctrl+Alt+2` to switch to translation template
2. Copy text: "Hello, how are you today?"
3. Press `Ctrl+Alt+Enter`
4. Get Spanish translation typed directly

### Model Management
1. Press `Ctrl+Alt+F8` to see available models
2. Models are copied to clipboard for easy reference
3. Edit `.env` file to change the active model

## 🤖 Supported Models

The app works with all Groq-compatible models including:
- `llama-3.1-8b-instant` (default - fast responses)
- `llama-3.1-70b-versatile` (more capable, slower)
- `mixtral-8x7b-32768` (good balance)
- And others available via Groq API

## 📊 Health Check

Run `Ctrl+Alt+F9` to get a comprehensive system report:
- ✅ **ENV**: API key validation
- ✅ **API_BASE**: URL and DNS resolution
- ✅ **AUTH**: Authentication status
- ✅ **MODELS**: Available models list
- ✅ **MODEL ACTIVE**: Current model validation
- ✅ **COMPLETION**: Test request with latency
- ✅ **RATE-LIMIT**: Rate limiting status
- ✅ **SERVER**: Server health

## 🎨 Customization

### Custom Templates
Create new templates in `%APPDATA%\ClipboardAI\templates\`:

```jinja2
<!-- custom.j2 -->
Act as a professional copywriter. Improve this text:

{{ content }}

Make it more engaging and persuasive.
```

### Typing Behavior
Adjust in `config.toml`:
```toml
[typewriter]
min_cps = 10          # Minimum characters per second
max_cps = 20          # Maximum characters per second
jitter_ms = 30        # Random delay variation
punct_pause_ms = 150  # Extra pause after punctuation
newline_pause_ms = 250 # Extra pause after newlines
```

### Privacy Patterns
Add custom privacy patterns:
```toml
[privacy]
blocked_patterns = [
    "sk-[A-Za-z0-9]{20,}",           # OpenAI keys
    "password\\s*=\\s*\\S+",         # Passwords
    "\\b\\d{4}-\\d{4}-\\d{4}-\\d{4}\\b" # Credit cards
]
```

## 🔄 Workflow Integration

### Code Review
1. Copy code snippet
2. Use with prompt: "Review this code for bugs and improvements"
3. Get detailed feedback typed directly into your IDE

### Email Writing
1. Copy rough email draft
2. Get AI-polished version typed into your email client
3. Review and send

### Translation
1. Switch to translate template (`Ctrl+Alt+2`)
2. Copy text in any language
3. Get Spanish translation typed directly

## 📋 Command Line Options

```bash
ClipboardAI.exe [options]

Options:
  --noconsole    Run without console window, log to file
  --help         Show help message
```

## 🐛 Reporting Issues

When reporting issues, please include:
1. Windows version
2. Output from diagnostics (`Ctrl+Alt+F9`)
3. Log file content (if using `--noconsole`)
4. Steps to reproduce

## 📜 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Groq API](https://groq.com/) for fast AI inference
- Uses [pynput](https://github.com/moses-palmer/pynput) for global hotkeys
- Powered by [httpx](https://github.com/encode/httpx) for async HTTP
- Rich terminal output via [rich](https://github.com/Textualize/rich)

## 🔗 Links

- [Groq Console](https://console.groq.com/) - Get your API key
- [GitHub Repository](https://github.com/yourusername/clipboard-ai)
- [Issue Tracker](https://github.com/yourusername/clipboard-ai/issues)
- [Releases](https://github.com/yourusername/clipboard-ai/releases)