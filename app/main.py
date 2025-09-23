import argparse
import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import pystray
from PIL import Image, ImageDraw
from pathlib import Path
import httpx

from app.ai_client import GroqClient
from app.clipboard import get_clipboard_text, set_clipboard_text
from app.config import load_config, save_env
from app.health import run_health_check
from app.hotkeys import register_hotkey, start_listening
from app.paste import typewrite
from app.prompts import render_template
from app.secrets_filter import is_blocked


def diagnostics_flow(config, client):
    report = run_health_check(config, client)
    print(report)
    set_clipboard_text(report)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--noconsole", action="store_true")
    args = parser.parse_args()

    if args.noconsole:
        log_path = Path.home() / "AppData" / "Roaming" / "ClipboardAI" / "logs.txt"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        sys.stdout = open(log_path, "a")

    config = load_config()

    if not config.api_key:
        show_settings_gui(config)
    else:
        start_app(config)


def show_settings_gui(config, client=None, from_tray=False):
    root = tk.Tk()
    root.title("Clipboard-AI Settings")
    root.geometry("600x500")
    root.resizable(False, False)

    # Center the window
    root.eval('tk::PlaceWindow . center')

    # Style
    style = ttk.Style()
    style.configure("TButton", padding=6, relief="flat", background="#ccc")
    style.configure("TLabel", padding=6)

    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill='both', padx=10, pady=10)

    # Tab 1: API & Model
    tab1 = ttk.Frame(notebook)
    notebook.add(tab1, text="API & Model")

    # API Key section
    api_frame = ttk.LabelFrame(tab1, text="API Configuration", padding="10")
    api_frame.pack(fill='x', padx=10, pady=10)

    ttk.Label(api_frame, text="Groq API Key:").grid(row=0, column=0, sticky=tk.W)
    api_entry = ttk.Entry(api_frame, width=50, show="*")
    api_entry.grid(row=1, column=0, pady=(5, 10))
    if config.api_key:
        api_entry.insert(0, config.api_key)

    scan_button = ttk.Button(api_frame, text="Scan Available Models")
    scan_button.grid(row=2, column=0, pady=(0, 10))
    if not api_entry.get().strip():
        scan_button.state(['disabled'])

    # Models section
    models_frame = ttk.LabelFrame(tab1, text="Model Selection", padding="10")
    models_frame.pack(fill='both', expand=True, padx=10, pady=10)

    ttk.Label(models_frame, text="Select Model:").grid(row=0, column=0, sticky=tk.W)
    model_combo = ttk.Combobox(models_frame, state="readonly")
    model_combo.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 10))

    # Pre-set current model if available
    if config.model:
        model_combo['values'] = [config.model]
        model_combo.set(config.model)

    # Enable/disable buttons based on API key
    def on_api_change(*args):
        if api_entry.get().strip():
            scan_button.state(['!disabled'])
        else:
            scan_button.state(['disabled'])
            model_combo['values'] = []
            model_combo.set('')

    api_entry_var = tk.StringVar()
    api_entry.config(textvariable=api_entry_var)
    api_entry_var.trace_add("write", on_api_change)

    def scan_models_local():
        api_key = api_entry.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter API key")
            return
        try:
            url = "https://api.groq.com/openai/v1/models"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            resp = httpx.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            models = [m['id'] for m in data['data']]
            print(f"DEBUG: Found {len(models)} models")
            model_combo['values'] = models
            # Select current if present
            if config.model in models:
                model_combo.set(config.model)
            else:
                model_combo.set('')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan models: {str(e)}")

    scan_button.config(command=scan_models_local)

    def save_settings():
        api_key = api_entry.get().strip()
        model = model_combo.get()
        if not api_key:
            messagebox.showerror("Error", "Please enter API key")
            return
        if not model:
            messagebox.showerror("Error", "Please select a model")
            return
        save_env(api_key, model)
        messagebox.showinfo("Saved", "Settings saved successfully!")
        if not from_tray:
            root.destroy()
            config = load_config()
            start_app(config)
        # If from_tray, just stay

    save_button.config(command=save_settings)

    # Tab 2: Hotkeys
    tab2 = ttk.Frame(notebook)
    notebook.add(tab2, text="Hotkeys")

    hotkeys_frame = ttk.LabelFrame(tab2, text="Keyboard Shortcuts", padding="10")
    hotkeys_frame.pack(fill='both', expand=True, padx=10, pady=10)

    ttk.Label(hotkeys_frame, text=f"Send: {config.hotkey_send}").grid(row=0, column=0, sticky=tk.W)
    ttk.Label(hotkeys_frame, text=f"Cancel: {config.hotkey_cancel}").grid(row=1, column=0, sticky=tk.W)
    ttk.Label(hotkeys_frame, text=f"List Models: {config.hotkey_list_models}").grid(row=2, column=0, sticky=tk.W)
    ttk.Label(hotkeys_frame, text=f"Diagnostics: {config.hotkey_diagnostics}").grid(row=3, column=0, sticky=tk.W)
    ttk.Label(hotkeys_frame, text=f"Template Default: {config.hotkey_template_default}").grid(row=4, column=0, sticky=tk.W)
    ttk.Label(hotkeys_frame, text=f"Template Translate: {config.hotkey_template_translate}").grid(row=5, column=0, sticky=tk.W)

    # Tab 3: Settings
    tab3 = ttk.Frame(notebook)
    notebook.add(tab3, text="Settings")

    settings_frame = ttk.LabelFrame(tab3, text="Application Settings", padding="10")
    settings_frame.pack(fill='both', expand=True, padx=10, pady=10)

    ttk.Label(settings_frame, text=f"Autopaste: {config.autopaste}").grid(row=0, column=0, sticky=tk.W)
    ttk.Label(settings_frame, text=f"Min CPS: {config.min_cps}").grid(row=1, column=0, sticky=tk.W)
    ttk.Label(settings_frame, text=f"Max CPS: {config.max_cps}").grid(row=2, column=0, sticky=tk.W)
    ttk.Label(settings_frame, text=f"Jitter MS: {config.jitter_ms}").grid(row=3, column=0, sticky=tk.W)
    ttk.Label(settings_frame, text=f"Punct Pause MS: {config.punct_pause_ms}").grid(row=4, column=0, sticky=tk.W)
    ttk.Label(settings_frame, text=f"Newline Pause MS: {config.newline_pause_ms}").grid(row=5, column=0, sticky=tk.W)
    ttk.Label(settings_frame, text=f"Preserve Clipboard: {config.preserve_clipboard}").grid(row=6, column=0, sticky=tk.W)
    ttk.Label(settings_frame, text=f"Timeout Seconds: {config.timeout_seconds}").grid(row=7, column=0, sticky=tk.W)
    ttk.Label(settings_frame, text=f"Max Retries: {config.max_retries}").grid(row=8, column=0, sticky=tk.W)

    # Tab 4: Diagnostics
    tab4 = ttk.Frame(notebook)
    notebook.add(tab4, text="Diagnostics")

    diag_frame = ttk.LabelFrame(tab4, text="Health Check", padding="10")
    diag_frame.pack(fill='both', expand=True, padx=10, pady=10)

    run_diag_button = ttk.Button(diag_frame, text="Run Diagnostics")
    run_diag_button.pack(pady=10)

    diag_text = tk.Text(diag_frame, height=10, width=60)
    diag_text.pack(fill='both', expand=True)

    def run_diagnostics():
        if client:
            diagnostics_flow(config, client)
            # Since it copies to clipboard, perhaps show in text
            diag_text.delete(1.0, tk.END)
            diag_text.insert(tk.END, "Diagnostics report copied to clipboard.")
        else:
            diag_text.delete(1.0, tk.END)
            diag_text.insert(tk.END, "API key required for diagnostics.")

    run_diag_button.config(command=run_diagnostics)

    # Buttons
    button_frame = ttk.Frame(root)
    button_frame.pack(pady=10)

    save_button = ttk.Button(button_frame, text="Save & Start" if not from_tray else "Save", command=save_settings)
    save_button.grid(row=0, column=0, padx=(0, 10))

    if from_tray:
        minimize_button = ttk.Button(button_frame, text="Minimize to Tray", command=lambda: root.withdraw())
        minimize_button.grid(row=0, column=1, padx=(0, 10))

    exit_button = ttk.Button(button_frame, text="Exit", command=lambda: os._exit(0))
    exit_button.grid(row=0, column=2)

    root.mainloop()


def show_setup_gui():
    root = tk.Tk()
    root.title("Clipboard-AI Setup")
    root.geometry("500x400")
    root.resizable(False, False)

    # Center the window
    root.eval('tk::PlaceWindow . center')

    # Style
    style = ttk.Style()
    style.configure("TButton", padding=6, relief="flat", background="#ccc")
    style.configure("TLabel", padding=6)

    # Main frame
    main_frame = ttk.Frame(root, padding="20")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Title
    title_label = ttk.Label(main_frame, text="Welcome to Clipboard-AI", font=("Arial", 16, "bold"))
    title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

    # API Key section
    api_frame = ttk.LabelFrame(main_frame, text="API Configuration", padding="10")
    api_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

    ttk.Label(api_frame, text="Enter your Groq API Key:").grid(row=0, column=0, sticky=tk.W)
    api_entry = ttk.Entry(api_frame, width=50, show="*")
    api_entry.grid(row=1, column=0, columnspan=2, pady=(5, 10))

    scan_button = ttk.Button(api_frame, text="Scan Available Models", command=lambda: scan_models(api_entry, model_listbox, save_button))
    scan_button.grid(row=2, column=0, columnspan=2, pady=(0, 10))
    scan_button.state(['disabled'])

    # Models section
    models_frame = ttk.LabelFrame(main_frame, text="Model Selection", padding="10")
    models_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))

    ttk.Label(models_frame, text="Available Models:").grid(row=0, column=0, sticky=tk.W)
    model_listbox = tk.Listbox(models_frame, height=8, width=50)
    scrollbar = ttk.Scrollbar(models_frame, orient=tk.VERTICAL, command=model_listbox.yview)
    model_listbox.configure(yscrollcommand=scrollbar.set)
    model_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))

    # Buttons
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=3, column=0, columnspan=2)

    save_button = ttk.Button(button_frame, text="Save & Start", command=lambda: save_and_start(api_entry, model_listbox, root))
    save_button.grid(row=0, column=0, padx=(0, 10))
    save_button.state(['disabled'])

    exit_button = ttk.Button(button_frame, text="Exit", command=root.quit)
    exit_button.grid(row=0, column=1)

    # Enable scan button when API key is entered
    def on_api_change(*args):
        if api_entry.get().strip():
            scan_button.state(['!disabled'])
        else:
            scan_button.state(['disabled'])
            model_listbox.delete(0, tk.END)
            save_button.state(['disabled'])

    api_entry_var = tk.StringVar()
    api_entry.config(textvariable=api_entry_var)
    api_entry_var.trace_add("write", on_api_change)

    root.mainloop()


def scan_models(api_entry, model_listbox, save_button):
    api_key = api_entry.get().strip()
    if not api_key:
        messagebox.showerror("Error", "Please enter API key")
        return
    try:
        url = "https://api.groq.com/openai/v1/models"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        resp = httpx.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        models = [m['id'] for m in data['data']]
        print(f"DEBUG: Found {len(models)} models")
        model_listbox.delete(0, tk.END)
        for model in models:
            model_listbox.insert(tk.END, model)
        # Enable save button
        save_button.state(['!disabled'])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to scan models: {str(e)}")


def save_and_start(api_entry, model_listbox, root):
    api_key = api_entry.get().strip()
    selected = model_listbox.curselection()
    if not api_key:
        messagebox.showerror("Error", "Please enter API key")
        return
    if not selected:
        messagebox.showerror("Error", "Please select a model")
        return
    model = model_listbox.get(selected[0])
    save_env(api_key, model)
    root.destroy()
    config = load_config()
    start_app(config)


def show_tray_icon(root):
    # Create a simple icon
    image = Image.new('RGB', (64, 64), color='blue')
    draw = ImageDraw.Draw(image)
    draw.rectangle([16, 16, 48, 48], fill='white')

    def show_window(icon, item):
        icon.stop()
        root.deiconify()

    def exit_app(icon, item):
        icon.stop()
        root.quit()

    menu = pystray.Menu(
        pystray.MenuItem("Show", show_window),
        pystray.MenuItem("Exit", exit_app)
    )

    icon = pystray.Icon("ClipboardAI", image, "Clipboard-AI", menu)
    icon.run()


def start_app(config):
    client = GroqClient(config)
    cancel_event = threading.Event()
    current_template = "default"

    def send_flow():
        print("DEBUG: Send hotkey pressed")
        text = get_clipboard_text()
        print(f"DEBUG: Clipboard text: {text[:50]}...")
        if is_blocked(text, config.blocked_patterns):
            print("DEBUG: Content blocked")
            return
        prompt = render_template(current_template, text)
        print(f"DEBUG: Prompt: {prompt[:50]}...")
        try:
            response = client.complete(prompt)
            print(f"DEBUG: Response: {response[:50]}...")
            typewrite(response, config, cancel_event)
        except Exception as e:
            print(f"DEBUG: Error: {e}")

    def cancel_flow():
        cancel_event.set()
        print("Typing cancelled")

    def list_models_flow():
        try:
            models = client.list_models()
            print("Models:", models)
            set_clipboard_text("\n".join(models))
        except Exception as e:
            print(f"Error listing models: {e}")

    def diagnostics_flow():
        report = run_health_check(config, client)
        print(report)
        set_clipboard_text(report)

    def set_template_default():
        nonlocal current_template
        current_template = "default"
        print("Template set to default")

    def set_template_translate():
        nonlocal current_template
        current_template = "translate_es"
        print("Template set to translate_es")

    # Register hotkeys
    register_hotkey(config.hotkey_send, send_flow)
    register_hotkey(config.hotkey_cancel, cancel_flow)
    register_hotkey(config.hotkey_list_models, list_models_flow)
    register_hotkey(config.hotkey_diagnostics, lambda: diagnostics_flow(config, client))
    register_hotkey(config.hotkey_template_default, set_template_default)
    register_hotkey(config.hotkey_template_translate, set_template_translate)

    # Create system tray
    def create_tray():
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        draw.rectangle([16, 16, 48, 48], fill='white')

        def exit_app(icon, item):
            icon.stop()
            os._exit(0)  # Force exit

        def set_model(model_name):
            config.model = model_name
            save_env(config.api_key, model_name)
            print(f"Model changed to {model_name}")

        def show_hotkeys(icon, item):
            hotkeys_text = (
                f"Send: {config.hotkey_send}\n"
                f"Cancel: {config.hotkey_cancel}\n"
                f"List Models: {config.hotkey_list_models}\n"
                f"Diagnostics: {config.hotkey_diagnostics}\n"
                f"Template Default: {config.hotkey_template_default}\n"
                f"Template Translate: {config.hotkey_template_translate}"
            )
            messagebox.showinfo("Hotkeys", hotkeys_text)

        def open_settings(icon, item):
            show_settings_gui(config, client, from_tray=True)

        try:
            models = client.list_models()
        except Exception as e:
            models = ["Error loading models"]
            print(f"Error loading models for tray: {e}")

        model_items = [pystray.MenuItem(model, lambda m=model: set_model(m)) for model in models]

        menu = pystray.Menu(
            pystray.MenuItem("Models", pystray.Menu(*model_items)),
            pystray.MenuItem("Settings", open_settings),
            pystray.MenuItem("Show Hotkeys", show_hotkeys),
            pystray.MenuItem("Exit", exit_app)
        )

        icon = pystray.Icon("ClipboardAI", image, "Clipboard-AI", menu)
        icon.run()

    tray_thread = threading.Thread(target=create_tray, daemon=True)
    tray_thread.start()

    print("Clipboard-AI started. Listening for hotkeys...")
    start_listening()


if __name__ == "__main__":
    main()
