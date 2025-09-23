import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import asyncio
import queue
import time
from pathlib import Path
import logging

from .config import Config, load_config, save_env_file
from .ai_client import GroqClient
from .health import run_health_check
from .clipboard import get_clipboard_text, set_clipboard_text


class ClipboardAIGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.config = None
        self.client = None
        self.logger = logging.getLogger("ClipboardAI.GUI")
        
        # Thread communication
        self.gui_queue = queue.Queue()
        self.background_tasks = []
        
        # State tracking
        self.models_cache = []
        self.last_health_check = None
        self.api_key_valid = False
        
        self.setup_window()
        self.create_widgets()
        self.load_initial_config()
        self.start_queue_processor()

    def setup_window(self):
        """Configure the main window."""
        self.root.title("Clipboard-AI Control Panel")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        self.root.minsize(600, 500)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.root.winfo_screenheight() // 2) - (600 // 2)
        self.root.geometry(f"700x600+{x}+{y}")
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        """Create all GUI widgets."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Header
        self.create_header(main_frame)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Create tabs
        self.create_api_tab()
        self.create_hotkeys_tab()
        self.create_settings_tab()
        self.create_diagnostics_tab()
        self.create_logs_tab()
        
        # Status bar
        self.create_status_bar(main_frame)

    def create_header(self, parent):
        """Create header with title and status."""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(header_frame, text="Clipboard-AI", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Status indicator
        self.status_frame = ttk.Frame(header_frame)
        self.status_frame.grid(row=0, column=1, sticky=tk.E)
        
        self.status_label = ttk.Label(self.status_frame, text="● Disconnected", 
                                     foreground="red")
        self.status_label.grid(row=0, column=0, padx=(0, 10))
        
        # Quick actions
        self.quick_test_btn = ttk.Button(self.status_frame, text="Quick Test",
                                        command=self.quick_test, width=12)
        self.quick_test_btn.grid(row=0, column=1)

    def create_api_tab(self):
        """Create API configuration tab."""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="API & Models")
        
        # API Key section
        api_group = ttk.LabelFrame(tab_frame, text="API Configuration", padding="10")
        api_group.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(api_group, text="Groq API Key:").pack(anchor=tk.W)
        
        key_frame = ttk.Frame(api_group)
        key_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(key_frame, textvariable=self.api_key_var, 
                                      show="*", width=50)
        self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.show_key_btn = ttk.Button(key_frame, text="👁", width=3,
                                      command=self.toggle_key_visibility)
        self.show_key_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # API key validation
        self.api_key_var.trace_add("write", self.on_api_key_change)
        
        # Models section
        models_group = ttk.LabelFrame(tab_frame, text="Model Selection", padding="10")
        models_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        model_controls = ttk.Frame(models_group)
        model_controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(model_controls, text="Active Model:").pack(side=tk.LEFT)
        
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(model_controls, textvariable=self.model_var,
                                       state="readonly", width=30)
        self.model_combo.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        self.refresh_models_btn = ttk.Button(model_controls, text="Refresh Models",
                                           command=self.refresh_models)
        self.refresh_models_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Models list
        ttk.Label(models_group, text="Available Models:").pack(anchor=tk.W)
        
        models_frame = ttk.Frame(models_group)
        models_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        self.models_tree = ttk.Treeview(models_frame, columns=("model",), show="tree headings", height=8)
        self.models_tree.heading("#0", text="Model ID")
        self.models_tree.column("#0", width=300)
        self.models_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        models_scroll = ttk.Scrollbar(models_frame, orient=tk.VERTICAL, command=self.models_tree.yview)
        models_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.models_tree.configure(yscrollcommand=models_scroll.set)
        
        # Double-click to select model
        self.models_tree.bind("<Double-1>", self.on_model_double_click)
        
        # Save button
        save_frame = ttk.Frame(tab_frame)
        save_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.save_btn = ttk.Button(save_frame, text="Save Configuration",
                                  command=self.save_config)
        self.save_btn.pack(side=tk.RIGHT)

    def create_hotkeys_tab(self):
        """Create hotkeys configuration tab."""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Hotkeys")
        
        hotkeys_group = ttk.LabelFrame(tab_frame, text="Keyboard Shortcuts", padding="10")
        hotkeys_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Hotkeys info (read-only for now)
        info_text = """Current Hotkeys (edit config.toml to change):

Send to AI:               Ctrl+Alt+Enter
Cancel Typing:           Ctrl+Alt+Backspace
List Models:             Ctrl+Alt+F8
Run Diagnostics:         Ctrl+Alt+F9
Default Template:        Ctrl+Alt+1
Translation Template:    Ctrl+Alt+2

Note: Restart the application after changing hotkeys in config.toml"""
        
        info_label = ttk.Label(hotkeys_group, text=info_text, justify=tk.LEFT)
        info_label.pack(anchor=tk.W)
        
        # Quick actions
        actions_frame = ttk.Frame(hotkeys_group)
        actions_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(actions_frame, text="Open Config Folder",
                  command=self.open_config_folder).pack(side=tk.LEFT)
        
        ttk.Button(actions_frame, text="Test Clipboard",
                  command=self.test_clipboard).pack(side=tk.LEFT, padx=(10, 0))

    def create_settings_tab(self):
        """Create settings tab."""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Settings")
        
        # Typewriter settings
        typing_group = ttk.LabelFrame(tab_frame, text="Typewriter Settings", padding="10")
        typing_group.pack(fill=tk.X, padx=10, pady=10)
        
        # Create a grid for settings
        settings_info = """Current Settings (edit config.toml to change):

Autopaste:               Enabled/Disabled
Typing Speed:            6-12 characters per second
Jitter:                  60ms random variation
Punctuation Pause:       220ms
Newline Pause:           150ms

Privacy Patterns:        Blocks API keys, passwords, tokens"""
        
        settings_label = ttk.Label(typing_group, text=settings_info, justify=tk.LEFT)
        settings_label.pack(anchor=tk.W)

    def create_diagnostics_tab(self):
        """Create diagnostics tab."""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Diagnostics")
        
        # Controls
        controls_frame = ttk.Frame(tab_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.run_diagnostics_btn = ttk.Button(controls_frame, text="Run Full Diagnostics",
                                             command=self.run_diagnostics)
        self.run_diagnostics_btn.pack(side=tk.LEFT)
        
        self.copy_report_btn = ttk.Button(controls_frame, text="Copy Report",
                                         command=self.copy_diagnostics_report)
        self.copy_report_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Results
        results_group = ttk.LabelFrame(tab_frame, text="Diagnostics Results", padding="10")
        results_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.diagnostics_text = scrolledtext.ScrolledText(results_group, height=15, 
                                                         font=("Consolas", 10))
        self.diagnostics_text.pack(fill=tk.BOTH, expand=True)

    def create_logs_tab(self):
        """Create logs tab."""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Logs")
        
        # Controls
        logs_controls = ttk.Frame(tab_frame)
        logs_controls.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(logs_controls, text="Clear Logs",
                  command=self.clear_logs).pack(side=tk.LEFT)
        
        ttk.Button(logs_controls, text="Refresh",
                  command=self.refresh_logs).pack(side=tk.LEFT, padx=(10, 0))
        
        # Log display
        logs_group = ttk.LabelFrame(tab_frame, text="Application Logs", padding="10")
        logs_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.logs_text = scrolledtext.ScrolledText(logs_group, height=15,
                                                  font=("Consolas", 9))
        self.logs_text.pack(fill=tk.BOTH, expand=True)

    def create_status_bar(self, parent):
        """Create status bar."""
        self.status_bar = ttk.Label(parent, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

    def load_initial_config(self):
        """Load initial configuration."""
        try:
            self.config = load_config()
            
            # Update GUI with config values
            if self.config.api_key:
                self.api_key_var.set(self.config.api_key)
                self.model_var.set(self.config.model)
                self.validate_api_key()
            
            self.update_status("Configuration loaded")
            
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            self.update_status("Failed to load configuration")

    def start_queue_processor(self):
        """Start the queue processor for thread communication."""
        def process_queue():
            try:
                while True:
                    try:
                        callback = self.gui_queue.get_nowait()
                        callback()
                    except queue.Empty:
                        break
            except Exception as e:
                self.logger.error(f"Queue processor error: {e}")
            
            # Schedule next check
            self.root.after(100, process_queue)
        
        process_queue()

    def run_in_background(self, func, *args, **kwargs):
        """Run a function in background thread and queue result."""
        def worker():
            try:
                result = func(*args, **kwargs)
                if result is not None:
                    self.gui_queue.put(lambda: self.handle_background_result(func.__name__, result))
            except Exception as e:
                self.gui_queue.put(lambda: self.handle_background_error(func.__name__, e))
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        self.background_tasks.append(thread)

    def handle_background_result(self, func_name, result):
        """Handle background task result."""
        if func_name == "fetch_models":
            self.models_cache = result
            self.update_models_display()
            self.update_status(f"Found {len(result)} models")
        elif func_name == "run_health_check":
            self.last_health_check = result
            self.display_diagnostics_result(result)

    def handle_background_error(self, func_name, error):
        """Handle background task error."""
        self.logger.error(f"Background task {func_name} failed: {error}")
        if func_name == "fetch_models":
            self.update_status(f"Failed to fetch models: {error}")
        elif func_name == "run_health_check":
            self.update_status(f"Diagnostics failed: {error}")

    def on_api_key_change(self, *args):
        """Handle API key changes."""
        # Debounce validation
        if hasattr(self, '_validation_job'):
            self.root.after_cancel(self._validation_job)
        
        self._validation_job = self.root.after(1000, self.validate_api_key)

    def validate_api_key(self):
        """Validate the API key."""
        api_key = self.api_key_var.get().strip()
        
        if not api_key:
            self.api_key_valid = False
            self.update_connection_status(False)
            return
        
        # Quick validation - create client and test
        try:
            temp_config = self.config._replace(api_key=api_key) if self.config else None
            if temp_config:
                self.client = GroqClient(temp_config)
                self.run_in_background(self.test_api_connection)
        except Exception as e:
            self.logger.error(f"API key validation error: {e}")
            self.api_key_valid = False
            self.update_connection_status(False)

    async def test_api_connection(self):
        """Test API connection."""
        try:
            if self.client:
                models = await self.client.list_models()
                self.api_key_valid = len(models) > 0
                return models
        except Exception as e:
            self.api_key_valid = False
            raise e

    def update_connection_status(self, connected):
        """Update connection status indicator."""
        if connected:
            self.status_label.config(text="● Connected", foreground="green")
        else:
            self.status_label.config(text="● Disconnected", foreground="red")

    def refresh_models(self):
        """Refresh the models list."""
        if not self.api_key_valid:
            messagebox.showerror("Error", "Please enter a valid API key first")
            return
        
        self.refresh_models_btn.config(state="disabled", text="Loading...")
        self.update_status("Fetching models...")
        
        async def fetch_models():
            if self.client:
                return await self.client.list_models()
            return []
        
        self.run_in_background(lambda: asyncio.run(fetch_models()))

    def update_models_display(self):
        """Update the models display."""
        # Clear existing items
        for item in self.models_tree.get_children():
            self.models_tree.delete(item)
        
        # Add models
        for model in self.models_cache:
            self.models_tree.insert("", "end", text=model)
        
        # Update combobox
        self.model_combo['values'] = self.models_cache
        
        # Re-enable button
        self.refresh_models_btn.config(state="normal", text="Refresh Models")

    def on_model_double_click(self, event):
        """Handle model double-click."""
        selection = self.models_tree.selection()
        if selection:
            model = self.models_tree.item(selection[0])['text']
            self.model_var.set(model)

    def quick_test(self):
        """Run a quick connectivity test."""
        if not self.api_key_var.get().strip():
            messagebox.showerror("Error", "Please enter an API key first")
            return
        
        self.quick_test_btn.config(state="disabled", text="Testing...")
        self.update_status("Running quick test...")
        
        def test():
            try:
                if self.client:
                    # Quick model list test
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    models = loop.run_until_complete(self.client.list_models())
                    return len(models) > 0
                return False
            except Exception:
                return False
        
        def on_result(success):
            self.quick_test_btn.config(state="normal", text="Quick Test")
            if success:
                self.update_connection_status(True)
                self.update_status("Connection test passed")
                messagebox.showinfo("Success", "API connection is working!")
            else:
                self.update_connection_status(False)
                self.update_status("Connection test failed")
                messagebox.showerror("Error", "API connection failed")
        
        self.run_in_background(lambda: on_result(test()))

    def run_diagnostics(self):
        """Run comprehensive diagnostics."""
        if not self.config or not self.client:
            messagebox.showerror("Error", "Configuration not loaded")
            return
        
        self.run_diagnostics_btn.config(state="disabled", text="Running...")
        self.diagnostics_text.delete(1.0, tk.END)
        self.diagnostics_text.insert(tk.END, "Running diagnostics...\n")
        self.update_status("Running diagnostics...")
        
        async def run_diag():
            return await run_health_check(self.config, self.client)
        
        self.run_in_background(lambda: asyncio.run(run_diag()))

    def display_diagnostics_result(self, result):
        """Display diagnostics result."""
        self.diagnostics_text.delete(1.0, tk.END)
        self.diagnostics_text.insert(tk.END, result)
        self.run_diagnostics_btn.config(state="normal", text="Run Full Diagnostics")
        self.update_status("Diagnostics completed")

    def copy_diagnostics_report(self):
        """Copy diagnostics report to clipboard."""
        if self.last_health_check:
            set_clipboard_text(self.last_health_check)
            self.update_status("Diagnostics report copied to clipboard")
        else:
            messagebox.showwarning("Warning", "No diagnostics report available")

    def save_config(self):
        """Save configuration."""
        api_key = self.api_key_var.get().strip()
        model = self.model_var.get().strip()
        
        if not api_key:
            messagebox.showerror("Error", "Please enter an API key")
            return
        
        if not model:
            messagebox.showerror("Error", "Please select a model")
            return
        
        try:
            save_env_file(api_key, model)
            self.update_status("Configuration saved")
            messagebox.showinfo("Success", "Configuration saved successfully!")
            
            # Reload config
            self.config = load_config()
            self.client = GroqClient(self.config)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")

    def toggle_key_visibility(self):
        """Toggle API key visibility."""
        if self.api_key_entry['show'] == '*':
            self.api_key_entry.config(show='')
            self.show_key_btn.config(text='🙈')
        else:
            self.api_key_entry.config(show='*')
            self.show_key_btn.config(text='👁')

    def open_config_folder(self):
        """Open configuration folder."""
        try:
            import os
            import subprocess
            config_dir = Path.home() / "AppData" / "Roaming" / "ClipboardAI"
            config_dir.mkdir(parents=True, exist_ok=True)
            
            if os.name == 'nt':  # Windows
                subprocess.run(['explorer', str(config_dir)])
            else:
                subprocess.run(['xdg-open', str(config_dir)])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open config folder: {e}")

    def test_clipboard(self):
        """Test clipboard functionality."""
        test_text = f"Clipboard test at {time.strftime('%H:%M:%S')}"
        if set_clipboard_text(test_text):
            retrieved = get_clipboard_text()
            if retrieved == test_text:
                messagebox.showinfo("Success", "Clipboard test passed!")
            else:
                messagebox.showerror("Error", "Clipboard test failed - data mismatch")
        else:
            messagebox.showerror("Error", "Failed to write to clipboard")

    def clear_logs(self):
        """Clear log display."""
        self.logs_text.delete(1.0, tk.END)

    def refresh_logs(self):
        """Refresh logs from file."""
        try:
            log_file = Path.home() / "AppData" / "Roaming" / "ClipboardAI" / "logs.txt"
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.logs_text.delete(1.0, tk.END)
                self.logs_text.insert(tk.END, content)
                self.logs_text.see(tk.END)
            else:
                self.logs_text.delete(1.0, tk.END)
                self.logs_text.insert(tk.END, "No log file found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read logs: {e}")

    def update_status(self, message):
        """Update status bar."""
        self.status_bar.config(text=message)
        self.root.update_idletasks()

    def on_closing(self):
        """Handle window closing."""
        # Cancel any pending background tasks
        for task in self.background_tasks:
            if task.is_alive():
                # Note: Can't directly kill threads, they need to finish naturally
                pass
        
        self.root.quit()
        self.root.destroy()

    def run(self):
        """Start the GUI main loop."""
        self.root.mainloop()


def create_gui():
    """Create and return GUI instance."""
    return ClipboardAIGUI()


def run_gui():
    """Run the GUI application."""
    gui = create_gui()
    gui.run()


if __name__ == "__main__":
    run_gui()