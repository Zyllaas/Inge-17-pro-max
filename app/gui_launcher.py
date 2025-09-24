#!/usr/bin/env python3
"""
Simple launcher for Clipboard-AI GUI.
This allows easy testing of the GUI without building.
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

try:
    from app.gui_integrated import run_gui
    
    if __name__ == "__main__":
        print("Starting Clipboard-AI GUI...")
        run_gui()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)