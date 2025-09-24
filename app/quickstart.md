# Clipboard-AI Quick Start Guide

## 🚀 Getting Started (2 minutes)

### Method 1: Run GUI for Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Launch GUI directly
python gui_launcher.py
```

### Method 2: Build and Install
```bash
# Build executable
build.bat

# Run the built executable
dist\ClipboardAI.exe
```

## ⚙️ First Time Setup

1. **Get API Key**: Sign up at [Groq Console](https://console.groq.com/) and get your API key

2. **Launch the App**: 
   - Double-click `ClipboardAI.exe` or run `python gui_launcher.py`

3. **Configure API**:
   - Go to "API & Models" tab
   - Enter your Groq API key
   - Click "Refresh Models" to load available models
   - Select a model (recommended: `llama-3.1-8b-instant`)
   - Click "Save Configuration"

4. **Start Hotkey Service**:
   - In the GUI header, click "Start Service"
   - Status should show "● Running" in green

5. **Test the Setup**:
   - Copy some text to clipboard
   - Press `Ctrl+Alt+Enter`
   - Watch AI response get typed!

## 🎮 Default Hotkeys

| Hotkey | Action |
|--------|--------|
| `Ctrl+Alt+Enter` | Send clipboard to AI → Type response |
| `Ctrl+Alt+Backspace` | Cancel typing |
| `Ctrl+Alt+F8` | List available models |
| `Ctrl+Alt+F9` | Run diagnostics |
| `Ctrl+Alt+1` | Switch to default template |
| `Ctrl+Alt+2` | Switch to Spanish translation |

## 🛠️ GUI Features

### Overview Tab
- **Service Status**: Start/stop hotkey service
- **Quick Actions**: Test connection, diagnostics, etc.
- **Status Cards**: API, model, template status

### API & Models Tab
- **API Configuration**: Enter and validate API key
- **Model Selection**: Browse and select AI models
- **Model Search**: Filter models by name

### Hotkeys Tab
- **Current Hotkeys**: View active hotkey mappings
- **Configuration**: Instructions for customizing hotkeys

### Settings Tab
- **Current Config**: View all configuration settings
- **File Locations**: Links to config files

### Diagnostics Tab
- **Health Checks**: Comprehensive system diagnostics
- **Connection Tests**: Verify API connectivity
- **Performance**: Response time monitoring

### Logs Tab
- **Real-time Logs**: View application logs
- **Troubleshooting**: Debug issues

## 🔧 Configuration Files

All configuration is stored in `%APPDATA%\ClipboardAI\`:

- **`.env`**: API key and model settings
- **`config.toml`**: Hotkeys, typewriter settings, privacy rules
- **`logs.txt`**: Application logs

## 🚨 Troubleshooting

### "No API key" error
- Go to API & Models tab
- Enter your Groq API key
- Click "Save Configuration"

### Hotkeys not working
- Check if service is running (green ● in header)
- Click "Start Service" if stopped
- Run diagnostics to check for conflicts

### Typing too fast/slow
- Edit `config.toml`
- Adjust `min_cps` and `max_cps` values
- Restart service

### Permission issues
- Run as administrator if needed
- Allow keyboard permissions when prompted

## 💡 Pro Tips

1. **Multiple Templates**: Create custom templates in `templates/` folder
2. **Privacy Protection**: Sensitive content (API keys, passwords) is automatically blocked
3. **Headless Mode**: Run `ClipboardAI.exe --headless` for background-only operation
4. **Model Performance**: 
   - `llama-3.1-8b-instant`: Fastest responses
   - `llama-3.1-70b-versatile`: Best quality
   - `mixtral-8x7b-32768`: Good balance

## 🏃‍♂️ Quick Workflow

1. **Copy text** you want AI to process
2. **Press `Ctrl+Alt+Enter`**
3. **Watch** as AI response gets typed automatically
4. **Press `Ctrl+Alt+Backspace`** to cancel if needed

---

**Need help?** Check the Diagnostics tab or view logs for troubleshooting.