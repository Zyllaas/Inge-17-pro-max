#!/usr/bin/env python3
"""
Setup script for development environment.
Run this to set up the development environment quickly.
"""

import os
import sys
import subprocess
import venv
from pathlib import Path


def run_command(cmd, check=True):
    """Run a command and handle errors."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False


def create_venv():
    """Create virtual environment."""
    venv_path = Path("venv")
    if venv_path.exists():
        print("Virtual environment already exists")
        return True
    
    print("Creating virtual environment...")
    try:
        venv.create("venv", with_pip=True)
        return True
    except Exception as e:
        print(f"Failed to create virtual environment: {e}")
        return False


def install_deps():
    """Install dependencies."""
    venv_python = "venv\\Scripts\\python.exe" if os.name == 'nt' else "venv/bin/python"
    venv_pip = "venv\\Scripts\\pip.exe" if os.name == 'nt' else "venv/bin/pip"
    
    commands = [
        f"{venv_pip} install --upgrade pip",
        f"{venv_pip} install -r requirements.txt",
        f"{venv_pip} install pyinstaller black ruff mypy"
    ]
    
    for cmd in commands:
        if not run_command(cmd):
            return False
    return True


def create_config_files():
    """Create initial config files if they don't exist."""
    files_to_create = [
        (".env.example", """API_BASE=https://api.groq.com/openai/v1
GROQ_API_KEY=
MODEL=llama-3.1-8b-instant"""),
        ("pyproject.toml", """[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
"""),
        ("LICENSE.txt", """MIT License

Copyright (c) 2024 Clipboard-AI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.""")
    ]
    
    for filename, content in files_to_create:
        if not Path(filename).exists():
            print(f"Creating {filename}")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)


def setup_directories():
    """Set up required directories."""
    dirs = [
        "app/utils",
        "templates", 
        "tests",
        "dist",
        "build",
        "out"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        
    # Create __init__.py files
    init_files = [
        "app/__init__.py",
        "app/utils/__init__.py", 
        "tests/__init__.py"
    ]
    
    for init_file in init_files:
        init_path = Path(init_file)
        if not init_path.exists():
            init_path.touch()


def main():
    """Main setup function."""
    print("Setting up Clipboard-AI development environment...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("Error: Python 3.11 or higher is required")
        sys.exit(1)
    
    # Setup steps
    steps = [
        ("Creating directories", setup_directories),
        ("Creating config files", create_config_files), 
        ("Creating virtual environment", create_venv),
        ("Installing dependencies", install_deps)
    ]
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            print(f"Failed: {step_name}")
            sys.exit(1)
        print(f"✓ {step_name} completed")
    
    print("\n" + "="*50)
    print("Setup completed successfully! 🎉")
    print("\nNext steps:")
    print("1. Add your Groq API key to .env.example and rename to .env")
    print("2. Run 'build.bat' to build the executable")
    print("3. Run tests with: venv\\Scripts\\python -m pytest tests\\")
    print("\nTo activate the virtual environment:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate.bat")
    else:
        print("   source venv/bin/activate")


if __name__ == "__main__":
    main()