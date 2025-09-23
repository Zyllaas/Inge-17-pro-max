import unittest
from app.secrets_filter import is_blocked
from app.prompts import render_template
from app.config import Config

class TestApp(unittest.TestCase):
    def test_is_blocked(self):
        patterns = ["sk-[A-Za-z0-9]{20,}", "password="]
        self.assertTrue(is_blocked("sk-12345678901234567890", patterns))
        self.assertTrue(is_blocked("password=secret", patterns))
        self.assertFalse(is_blocked("hello world", patterns))

    def test_render_template(self):
        result = render_template("default", "Hello")
        self.assertEqual(result, "Hello")

    def test_config(self):
        # Mock config
        config = Config(
            hotkey_send="ctrl+alt+enter",
            hotkey_cancel="ctrl+alt+backspace",
            hotkey_list_models="ctrl+alt+`",
            hotkey_diagnostics="ctrl+alt+d",
            hotkey_template_default="ctrl+alt+1",
            hotkey_template_translate="ctrl+alt+2",
            autopaste=False,
            min_cps=6,
            max_cps=12,
            jitter_ms=60,
            punct_pause_ms=220,
            newline_pause_ms=150,
            preserve_clipboard=True,
            timeout_seconds=60,
            max_retries=3,
            blocked_patterns=["sk-", "password="],
            api_base="https://api.groq.com/openai/v1",
            api_key="test_key",
            model="test_model"
        )
        self.assertEqual(config.api_key, "test_key")

if __name__ == '__main__':
    unittest.main()