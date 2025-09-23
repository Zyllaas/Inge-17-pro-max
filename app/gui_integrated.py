import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import asyncio
import queue
import time
from pathlib import Path
import logging
import sys
import os

from .config import Config, load_config, save_env_file
from .ai_client import GroqClient
from .app_manager import AppManager


class ClipboardAIGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.config = None
        self.app_manager = None
        self.logger = logging.getLogger("ClipboardAI.GUI")
        
        # Thread communication
        self.gui_queue = queue.Queue()
        self.background_tasks = []
        
        # State tracking
        self.models_cache = []
        self.last_health_check = None
        self.service_running = False
        
        self.setup_window()
        self.create_widgets()
        self.load_initial_config()
        self.start_queue_processor()
        
        # Check for existing hybrid app
        self.check_hybrid_app()

    def check_hybrid_app(self):
        """Check if there's an existing hybrid app and integrate with it."""
        try:
            # Import here to avoid circular imports
            from .main import get_hybrid_app
            hybrid_app = get_hybrid_app()
            
            if hybrid_app and hybrid_app.running:
                self.app_manager = hybrid_app.get_app_manager()
                self.service_running = True
                self.update_service_status()
                self.logger.info("Connected to existing background service")
        except Exception as e:
            self.logger.debug(f"No existing hybrid app: {e}")

    def setup_window(self):
        """Configure the main window."""
        self.root.title("Clipboard-AI Control Panel")
        self.root.geometry("800x650")
        self.root.resizable(True, True)
        self.root.minsize(700, 500)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.root.winfo_screenheight() // 2) - (650 // 2)
        self.root.geometry(f"800x650+{x}+{y}")
        
        # Configure style
        style = ttk.Style()
        available_themes = style.theme_names()
        if 'vista' in available_themes:
            style.theme_use('vista')
        elif 'clam' in available_themes:
            style.theme_use('clam')
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        """Create all GUI widgets."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="15")
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
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(15, 0))
        
        # Create tabs
        self.create_overview_tab()
        self.create_api_tab()
        self.create_hotkeys_tab()
        self.create_settings_tab()
        self.create_diagnostics_tab()
        self.create_logs_tab()
        
        # Status bar
        self.create_status_bar(main_frame)

    def create_header(self, parent):
        """Create header with title and controls."""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        header_frame.columnconfigure(1, weight=1)
        
        # Title and version
        title_frame = ttk.Frame(header_frame)
        title_frame.grid(row=0, column=0, sticky=tk.W)
        
        title_label = ttk.Label(title_frame, text="Clipboard-AI", 
                               font=("Segoe UI", 18, "bold"))
        title_label.pack(anchor=tk.W)
        
        version_label = ttk.Label(title_frame, text="Control Panel v1.0", 
                                 font=("Segoe UI", 9), foreground="gray")
        version_label.pack(anchor=tk.W)
        
        # Service status and controls
        self.service_frame = ttk.LabelFrame(header_frame, text="Hotkey Service", padding="10")
        self.service_frame.grid(row=0, column=1, sticky=tk.E, padx=(20, 0))
        
        status_row = ttk.Frame(self.service_frame)
        status_row.pack(fill=tk.X)
        
        self.service_status_label = ttk.Label(status_row, text="● Stopped", foreground="red")
        self.service_status_label.pack(side=tk.LEFT)
        
        self.service_toggle_btn = ttk.Button(status_row, text="Start Service",
                                           command=self.toggle_service, width=12)
        self.service_toggle_btn.pack(side=tk.RIGHT, padx=(10, 0))

    def create_overview_tab(self):
        """Create overview tab."""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Overview")
        
        # Quick status cards
        cards_frame = ttk.Frame(tab_frame)
        cards_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # API Status Card
        api_card = ttk.LabelFrame(cards_frame, text="API Status", padding="10")
        api_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.api_status_text = ttk.Label(api_card, text="Not configured", 
                                        font=("Segoe UI", 10))
        self.api_status_text.pack()
        
        # Model Card
        model_card = ttk.LabelFrame(cards_frame, text="Current Model", padding="10")
        model_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.model_status_text = ttk.Label(model_card, text="None selected",
                                          font=("Segoe UI", 10))
        self.model_status_text.pack()
        
        # Template Card
        template_card = ttk.LabelFrame(cards_frame, text="Active Template", padding="10")
        template_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.template_status_text = ttk.Label(template_card, text="default",
                                             font=("Segoe UI", 10))
        self.template_status_text.pack()
        
        # Quick Actions
        actions_frame = ttk.LabelFrame(tab_frame, text="Quick Actions", padding="15")
        actions_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Action buttons in a grid
        btn_frame = ttk.Frame(actions_frame)
        btn_frame.pack()
        
        ttk.Button(btn_frame, text="Test Connection", 
                  command=self.quick_test, width=15).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(btn_frame, text="Test Clipboard", 
                  command=self.test_clipboard, width=15).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(btn_frame, text="Run Diagnostics", 
                  command=self.run_diagnostics, width=15).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(btn_frame, text="Open Config Folder", 
                  command=self.open_config_folder, width=15).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(btn_frame, text="Refresh Models", 
                  command=self.refresh_models, width=15).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(btn_frame, text="View Logs", 
                  command=lambda: self.notebook.select(5), width=15).grid(row=1, column=2, padx=5, pady=5)
        
        # Hotkeys reference
        hotkeys_frame = ttk.LabelFrame(tab_frame, text="Active Hotkeys", padding="15")
        hotkeys_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.hotkeys_text = tk.Text(hotkeys_frame, height=8, font=("Consolas", 10),
                                   state=tk.DISABLED, bg=self.root.cget('bg'))
        self.hotkeys_text.pack(fill=tk.BOTH, expand=True)

    def create_api_tab(self):
        """Create API configuration tab."""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="API & Models")
        
        # Scrollable frame
        canvas = tk.Canvas(tab_frame)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # API Key section
        api_group = ttk.LabelFrame(scrollable_frame, text="API Configuration", padding="15")
        api_group.pack(fill=tk.X, padx=15, pady=15)
        
        ttk.Label(api_group, text="Groq API Key:").pack(anchor=tk.W)
        
        key_frame = ttk.Frame(api_group)
        key_frame.pack(fill=tk.X, pady=(8, 15))
        
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(key_frame, textvariable=self.api_key_var, 
                                      show="*", font=("Consolas", 10))
        self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.show_key_btn = ttk.Button(key_frame, text="👁", width=4,
                                      command=self.toggle_key_visibility)
        self.show_key_btn.pack(side=tk.RIGHT, padx=(8, 0))
        
        # Validation feedback
        self.key_feedback = ttk.Label(api_group, text="")
        self.key_feedback.pack(anchor=tk.W)
        
        # API key validation with debouncing
        self.api_key_var.trace_add("write", self.on_api_key_change)
        
        # Models section
        models_group = ttk.LabelFrame(scrollable_frame, text="Model Management", padding="15")
        models_group.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Model selection
        model_select_frame = ttk.Frame(models_group)
        model_select_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(model_select_frame, text="Active Model:").pack(side=tk.LEFT)
        
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(model_select_frame, textvariable=self.model_var,
                                       state="readonly", width=40)
        self.model_combo.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        self.refresh_models_btn = ttk.Button(model_select_frame, text="Refresh",
                                           command=self.refresh_models, width=10)
        self.refresh_models_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Models list with search
        search_frame = ttk.Frame(models_group)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.model_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.model_search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(10, 0))
        self.model_search_var.trace_add("write", self.filter_models)
        
        # Models tree
        tree_frame = ttk.Frame(models_group)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.models_tree = ttk.Treeview(tree_frame, columns=("info",), show="tree headings", height=10)
        self.models_tree.heading("#0", text="Model ID")
        self.models_tree.heading("info", text="Info")
        self.models_tree.column("#0", width=300)
        self.models_tree.column("info", width=200)
        
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.models_tree.yview)
        self.models_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.models_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click to select
        self.models_tree.bind("<Double-1>", self.on_model_double_click)
        
        # Pack scrollable content
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Save configuration section (fixed at bottom)
        save_frame = ttk.Frame(tab_frame)
        save_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=15, pady=15)
        
        self.save_btn = ttk.Button(save_frame, text="Save Configuration",
                                  command=self.save_config)
        self.save_btn.pack(side=tk.RIGHT)

    def create_hotkeys_tab(self):
        """Create hotkeys tab."""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Hotkeys")
        
        # Current hotkeys display
        current_group = ttk.LabelFrame(tab_frame, text="Current Hotkeys", padding="15")
        current_group.pack(fill=tk.X, padx=15, pady=15)
        
        self.hotkeys_display = tk.Text(current_group, height=12, font=("Consolas", 11),
                                      state=tk.DISABLED, bg=self.root.cget('bg'))
        self.hotkeys_display.pack(fill=tk.X)
        
        # Instructions
        instructions_group = ttk.LabelFrame(tab_frame, text="Configuration", padding="15")
        instructions_group.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        instructions_text = """How to modify hotkeys:

1. Click "Open Config Folder" below
2. Edit the file "config.toml" 
3. Modify the hotkey strings under [app] section
4. Restart the application or restart the hotkey service

Hotkey format examples:
• "ctrl+alt+enter"
• "ctrl+shift+f1" 
• "alt+f8"

Supported keys: ctrl, alt, shift, enter, backspace, f1-f12, a-z, 0-9"""
        
        instructions_label = ttk.Label(instructions_group, text=instructions_text, 
                                     justify=tk.LEFT, font=("Segoe UI", 10))
        instructions_label.pack(anchor=tk.W)
        
        # Action buttons
        actions_frame = ttk.Frame(instructions_group)
        actions_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(actions_frame, text="Open Config Folder",
                  command=self.open_config_folder).pack(side=tk.LEFT)
        
        ttk.Button(actions_frame, text="Restart Service",
                  command=self.restart_service).pack(side=tk.LEFT, padx=(10, 0))

    def create_settings_tab(self):
        """Create settings tab."""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Settings")
        
        # Current settings display
        settings_group = ttk.LabelFrame(tab_frame, text="Current Settings", padding="15")
        settings_group.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.settings_text = scrolledtext.ScrolledText(settings_group, height=20, 
                                                      font=("Consolas", 10), state=tk.DISABLED)
        self.settings_text.pack(fill=tk.BOTH, expand=True)

    def create_diagnostics_tab(self):
        """Create diagnostics tab."""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Diagnostics")
        
        # Controls
        controls_frame = ttk.Frame(tab_frame)
        controls_frame.pack(fill=tk.X, padx=15, pady=15)
        
        self.run_diagnostics_btn = ttk.Button(controls_frame, text="Run Full Diagnostics",
                                             command=self.run_diagnostics, width=20)
        self.run_diagnostics_btn.pack(side=tk.LEFT)
        
        self.copy_report_btn = ttk.Button(controls_frame, text="Copy Report",
                                         command=self.copy_diagnostics_report, width=12)
        self.copy_report_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Auto-refresh toggle
        self.auto_refresh_var = tk.BooleanVar()
        auto_refresh_cb = ttk.Checkbutton(controls_frame, text="Auto-refresh (30s)",
                                         variable=self.auto_refresh_var,
                                         command=self.toggle_auto_refresh)
        auto_refresh_cb.pack(side=tk.RIGHT)
        
        # Results
        results_group = ttk.LabelFrame(tab_frame, text="Diagnostics Results", padding="15")
        results_group.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.diagnostics_text = scrolledtext.ScrolledText(results_group, height=18, 
                                                         font=("Consolas", 10))
        self.diagnostics_text.pack(fill=tk.BOTH, expand=True)

    def create_logs_tab(self):
        """Create logs tab."""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Logs")
        
        # Controls
        logs_controls = ttk.Frame(tab_frame)
        logs_controls.pack(fill=tk.X, padx=15, pady=15)
        
        ttk.Button(logs_controls, text="Clear Logs",
                  command=self.clear_logs, width=12).pack(side=tk.LEFT)
        
        ttk.Button(logs_controls, text="Refresh",
                  command=self.refresh_logs, width=12).pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(logs_controls, text="Open Log File",
                  command=self.open_log_file, width=12).pack(side=tk.LEFT, padx=(10, 0))
        
        # Auto-scroll toggle
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(logs_controls, text="Auto-scroll",
                       variable=self.auto_scroll_var).pack(side=tk.RIGHT)
        
        # Log display
        logs_group = ttk.LabelFrame(tab_frame, text="Application Logs", padding="15")
        logs_group.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.logs_text = scrolledtext.ScrolledText(logs_group, height=18,
                                                  font=("Consolas", 9))
        self.logs_text.pack(fill=tk.BOTH, expand=True)

    def create_status_bar(self, parent):
        """Create status bar."""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(15, 0))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_bar = ttk.Label(status_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Connection indicator
        self.connection_indicator = ttk.Label(status_frame, text="●", foreground="gray")
        self.connection_indicator.pack(side=tk.RIGHT, padx=(10, 0))

    def load_initial_config(self):
        """Load initial configuration."""
        try:
            self.config = load_config()
            
            # Update GUI with config values
            if self.config.api_key:
                self.api_key_var.set(self.config.api_key)
                self.model_var.set(self.config.model)
                self.validate_api_key_delayed()
            
            self.update_status("Configuration loaded")
            self.update_displays()
            
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            self.update_status("Failed to load configuration")

    def update_displays(self):
        """Update all display elements with current config."""
        if not self.config:
            return
        
        # Update overview cards
        if hasattr(self, 'api_status_text'):
            status = "Configured" if self.config.api_key else "Not configured"
            self.api_status_text.config(text=status)
        
        if hasattr(self, 'model_status_text'):
            self.model_status_text.config(text=self.config.model or "None")
        
        # Update hotkeys display
        self.update_hotkeys_display()
        self.update_settings_display()

    def update_hotkeys_display(self):
        """Update hotkeys display."""
        if not self.config:
            return
        
        hotkeys_info = f"""Active Hotkeys:

Send to AI:               {self.config.hotkey_send}
Cancel Typing:           {self.config.hotkey_cancel}
List Models:             {self.config.hotkey_list_models}
Run Diagnostics:         {self.config.hotkey_diagnostics}
Default Template:        {self.config.hotkey_template_default}
Translation Template:    {self.config.hotkey_template_translate}

Service Status: {'Running' if self.service_running else 'Stopped'}
Autopaste: {'Enabled' if self.config.autopaste else 'Disabled'}"""
        
        # Update overview hotkeys
        if hasattr(self, 'hotkeys_text'):
            self.hotkeys_text.config(state=tk.NORMAL)
            self.hotkeys_text.delete(1.0, tk.END)
            self.hotkeys_text.insert(tk.END, hotkeys_info)
            self.hotkeys_text.config(state=tk.DISABLED)
        
        # Update hotkeys tab
        if hasattr(self, 'hotkeys_display'):
            self.hotkeys_display.config(state=tk.NORMAL)
            self.hotkeys_display.delete(1.0, tk.END)
            self.hotkeys_display.insert(tk.END, hotkeys_info)
            self.hotkeys_display.config(state=tk.DISABLED)

    def update_settings_display(self):
        """Update settings display."""
        if not self.config or not hasattr(self, 'settings_text'):
            return
        
        settings_info = f"""Configuration Settings:

[API]
Base URL: {self.config.api_base}
Model: {self.config.model}
Timeout: {self.config.timeout_seconds} seconds
Max Retries: {self.config.max_retries}

[Typewriter]
Autopaste: {self.config.autopaste}
Min Speed: {self.config.min_cps} characters/second
Max Speed: {self.config.max_cps} characters/second
Jitter: {self.config.jitter_ms}ms
Punctuation Pause: {self.config.punct_pause_ms}ms
Newline Pause: {self.config.newline_pause_ms}ms
Preserve Clipboard: {self.config.preserve_clipboard}

[Privacy]
Blocked Patterns: {len(self.config.blocked_patterns)} patterns
- {chr(10).join(self.config.blocked_patterns[:3])}
{'...' if len(self.config.blocked_patterns) > 3 else ''}

To modify these settings, edit config.toml in the configuration folder."""
        
        self.settings_text.config(state=tk.NORMAL)
        self.settings_text.delete(1.0, tk.END)
        self.settings_text.insert(tk.END, settings_info)
        self.settings_text.config(state=tk.DISABLED)

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
        elif func_name == "run_health_check_async":
            self.last_health_check = result
            self.display_diagnostics_result(result)
        elif func_name == "test_connection":
            success, message = result
            self.update_connection_status(success, message)

    def handle_background_error(self, func_name, error):
        """Handle background task error."""
        self.logger.error(f"Background task {func_name} failed: {error}")
        if func_name == "fetch_models":
            self.update_status(f"Failed to fetch models: {error}")
            self.refresh_models_btn.config(state="normal", text="Refresh")
        elif func_name == "run_health_check_async":
            self.update_status(f"Diagnostics failed: {error}")
            self.run_diagnostics_btn.config(state="normal", text="Run Full Diagnostics")

    def on_api_key_change(self, *args):
        """Handle API key changes with debouncing."""
        if hasattr(self, '_validation_job'):
            self.root.after_cancel(self._validation_job)
        
        self._validation_job = self.root.after(1500, self.validate_api_key_delayed)

    def validate_api_key_delayed(self):
        """Validate API key with delay."""
        api_key = self.api_key_var.get().strip()
        
        if not api_key:
            self.key_feedback.config(text="", foreground="red")
            self.update_connection_status(False, "No API key")
            return
        
        if len(api_key) < 20:
            self.key_feedback.config(text="⚠ API key seems too short", foreground="orange")
            return
        
        self.key_feedback.config(text="🔄 Validating...", foreground="blue")
        
        # Test the key
        self.run_in_background(self.test_api_key, api_key)

    def test_api_key(self, api_key):
        """Test API key validity."""
        try:
            from .ai_client import GroqClient
            temp_config = self.config._replace(api_key=api_key) if self.config else None
            if temp_config:
                client = GroqClient(temp_config)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                models = loop.run_until_complete(client.list_models())
                loop.close()
                return True, f"Valid - {len(models)} models available"
        except Exception as e:
            return False, f"Invalid: {str(e)}"

    def update_connection_status(self, connected, message=""):
        """Update connection status."""
        if connected:
            self.connection_indicator.config(text="●", foreground="green")
            self.key_feedback.config(text=f"✓ {message}", foreground="green")
        else:
            self.connection_indicator.config(text="●", foreground="red")
            if message:
                self.key_feedback.config(text=f"✗ {message}", foreground="red")

    def toggle_service(self):
        """Toggle the hotkey service."""
        if self.service_running:
            self.stop_service()
        else:
            self.start_service()

    def start_service(self):
        """Start the hotkey service."""
        if not self.config or not self.config.api_key:
            messagebox.showerror("Error", "Please configure API key first")
            return
        
        try:
            self.app_manager = AppManager(self.config)
            
            def service_worker():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.app_manager.start_async())
            
            self.service_thread = threading.Thread(target=service_worker, daemon=True)
            self.service_thread.start()
            
            self.service_running = True
            self.update_service_status()
            self.update_status("Hotkey service started")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start service: {e}")

    def stop_service(self):
        """Stop the hotkey service."""
        if self.app_manager:
            self.app_manager.stop()
        
        self.service_running = False
        self.update_service_status()
        self.update_status("Hotkey service stopped")

    def restart_service(self):
        """Restart the hotkey service."""
        if self.service_running:
            self.stop_service()
            time.sleep(1)
        
        # Reload config
        self.load_initial_config()
        self.start_service()

    def update_service_status(self):
        """Update service status display."""
        if self.service_running:
            self.service_status_label.config(text="● Running", foreground="green")
            self.service_toggle_btn.config(text="Stop Service")
        else:
            self.service_status_label.config(text="● Stopped", foreground="red")
            self.service_toggle_btn.config(text="Start Service")
        
        self.update_hotkeys_display()

    def refresh_models(self):
        """Refresh models list."""
        if not self.config or not self.config.api_key:
            messagebox.showerror("Error", "Please configure API key first")
            return
        
        self.refresh_models_btn.config(state="disabled", text="Loading...")
        self.update_status("Fetching models...")
        
        self.run_in_background(self.fetch_models)

    def fetch_models(self):
        """Fetch models from API."""
        try:
            client = GroqClient(self.config)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            models = loop.run_until_complete(client.list_models())
            loop.close()
            return models
        except Exception as e:
            raise e

    def update_models_display(self):
        """Update models display."""
        # Clear existing
        for item in self.models_tree.get_children():
            self.models_tree.delete(item)
        
        # Add models
        for model in self.models_cache:
            # Simple categorization
            if "8b" in model:
                info = "8B params - Fast"
            elif "70b" in model:
                info = "70B params - Capable"
            elif "mixtral" in model:
                info = "Mixtral - Balanced"
            else:
                info = "General purpose"
            
            self.models_tree.insert("", "end", text=model, values=(info,))
        
        # Update combobox
        self.model_combo['values'] = self.models_cache
        
        # Re-enable button
        self.refresh_models_btn.config(state="normal", text="Refresh")

    def filter_models(self, *args):
        """Filter models based on search."""
        search_term = self.model_search_var.get().lower()
        
        # Clear existing
        for item in self.models_tree.get_children():
            self.models_tree.delete(item)
        
        # Add filtered models
        for model in self.models_cache:
            if search_term in model.lower():
                if "8b" in model:
                    info = "8B params - Fast"
                elif "70b" in model:
                    info = "70B params - Capable"
                elif "mixtral" in model:
                    info = "Mixtral - Balanced"
                else:
                    info = "General purpose"
                
                self.models_tree.insert("", "end", text=model, values=(info,))

    def on_model_double_click(self, event):
        """Handle model selection."""
        selection = self.models_tree.selection()
        if selection:
            model = self.models_tree.item(selection[0])['text']
            self.model_var.set(model)
            self.update_status(f"Selected model: {model}")

    def quick_test(self):
        """Quick connection test."""
        if not self.config or not self.config.api_key:
            messagebox.showerror("Error", "Please configure API key first")
            return
        
        self.update_status("Testing connection...")
        self.run_in_background(self.test_connection)

    def test_connection(self):
        """Test API connection."""
        try:
            client = GroqClient(self.config)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            models = loop.run_until_complete(client.list_models())
            loop.close()
            return True, f"Connected - {len(models)} models"
        except Exception as e:
            return False, str(e)

    def run_diagnostics(self):
        """Run diagnostics."""
        if not self.config:
            messagebox.showerror("Error", "Configuration not loaded")
            return
        
        self.run_diagnostics_btn.config(state="disabled", text="Running...")
        self.diagnostics_text.delete(1.0, tk.END)
        self.diagnostics_text.insert(tk.END, "Running diagnostics...\n")
        self.update_status("Running diagnostics...")
        
        self.run_in_background(self.run_health_check_async)

    def run_health_check_async(self):
        """Run health check asynchronously."""
        try:
            from .health import run_health_check
            client = GroqClient(self.config)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(run_health_check(self.config, client))
            loop.close()
            return result
        except Exception as e:
            raise e

    def display_diagnostics_result(self, result):
        """Display diagnostics result."""
        self.diagnostics_text.delete(1.0, tk.END)
        self.diagnostics_text.insert(tk.END, result)
        self.run_diagnostics_btn.config(state="normal", text="Run Full Diagnostics")
        self.update_status("Diagnostics completed")

    def copy_diagnostics_report(self):
        """Copy diagnostics to clipboard."""
        if self.last_health_check:
            from .clipboard import set_clipboard_text
            set_clipboard_text(self.last_health_check)
            self.update_status("Report copied to clipboard")
        else:
            messagebox.showwarning("Warning", "No report available")

    def toggle_auto_refresh(self):
        """Toggle auto-refresh for diagnostics."""
        # Implementation for auto-refresh
        pass

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
            messagebox.showinfo("Success", "Configuration saved!\n\nRestart the service to apply changes.")
            
            # Reload config
            self.config = load_config()
            self.update_displays()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

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
            config_dir = Path.home() / "AppData" / "Roaming" / "ClipboardAI"
            config_dir.mkdir(parents=True, exist_ok=True)
            
            if sys.platform == "win32":
                os.startfile(config_dir)
            else:
                import subprocess
                subprocess.run(['xdg-open', str(config_dir)])
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")

    def open_log_file(self):
        """Open log file."""
        try:
            log_file = Path.home() / "AppData" / "Roaming" / "ClipboardAI" / "logs.txt"
            
            if log_file.exists():
                if sys.platform == "win32":
                    os.startfile(log_file)
                else:
                    import subprocess
                    subprocess.run(['xdg-open', str(log_file)])
            else:
                messagebox.showinfo("Info", "No log file found")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open log file: {e}")

    def test_clipboard(self):
        """Test clipboard functionality."""
        from .clipboard import get_clipboard_text, set_clipboard_text
        
        test_text = f"Clipboard test - {time.strftime('%H:%M:%S')}"
        
        if set_clipboard_text(test_text):
            retrieved = get_clipboard_text()
            if retrieved == test_text:
                messagebox.showinfo("Success", "✓ Clipboard test passed!")
                self.update_status("Clipboard test successful")
            else:
                messagebox.showerror("Error", "✗ Clipboard test failed - data mismatch")
        else:
            messagebox.showerror("Error", "✗ Failed to write to clipboard")

    def clear_logs(self):
        """Clear log display."""
        self.logs_text.delete(1.0, tk.END)

    def refresh_logs(self):
        """Refresh logs display."""
        try:
            log_file = Path.home() / "AppData" / "Roaming" / "ClipboardAI" / "logs.txt"
            
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.logs_text.delete(1.0, tk.END)
                self.logs_text.insert(tk.END, content)
                
                if self.auto_scroll_var.get():
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
        if self.service_running:
            result = messagebox.askyesnocancel(
                "Clipboard-AI", 
                "The hotkey service is running.\n\nStop service and exit?"
            )
            if result is True:
                self.stop_service()
            elif result is None:
                return  # Cancel close
        
        self.root.quit()
        self.root.destroy()

    def run(self):
        """Start the GUI."""
        self.root.mainloop()


def run_gui():
    """Run the GUI application."""
    gui = ClipboardAIGUI()
    gui.run()


if __name__ == "__main__":
    run_gui()