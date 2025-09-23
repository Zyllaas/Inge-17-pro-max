@echo off
pyinstaller -n ClipboardAI --onefile --noconsole --add-data "templates;templates" --add-data "config.toml;." --add-data ".env.example;." app/main.py