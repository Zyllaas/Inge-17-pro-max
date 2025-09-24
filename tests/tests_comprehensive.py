import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the app directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.secrets_filter import is_blocked, validate_patterns
from app.prompts import TemplateManager
from app.config import Config
from app.ai_client import GroqClient
from app.clipboard import get_clipboard_text, set_clipboard_text
from app.hotkeys import HotkeyManager


class TestSecretsFilter(unittest.TestCase):
    def test_blocked_patterns(self):
        """Test privacy filter blocks sensitive patterns."""
        patterns = [
            r"sk-[A-Za-z0-9]{20,}",
            r"password\s*=\s*\S+",
            r"Authorization:\s*Bearer\s+\S+"
        ]
        
        # Should be blocked
        self.assertTrue(is_blocked("sk-12345678901234567890abc", patterns))
        self.assertTrue(is_blocked("password=mysecret", patterns))
        self.assertTrue(is_blocked("Authorization: Bearer abc123", patterns))
        
        # Should not be blocked
        self.assertFalse(is_blocked("Hello world", patterns))
        self.assertFalse(is_blocked("sk-short", patterns))
        self.assertFalse(is_blocked("just some text", patterns))

    def test_validate_patterns(self):
        """Test pattern validation."""
        patterns = [
            r"valid-pattern",
            r"[invalid-pattern",  # Invalid regex
            r"another-valid-pattern"
        ]
        
        valid = validate_patterns(patterns)
        self.assertEqual(len(valid), 2)
        self.assertIn(r"valid-pattern", valid)
        self.assertIn(r"another-valid-pattern", valid)
        self.assertNotIn(r"[invalid-pattern", valid)


class TestTemplateManager(unittest.TestCase):
    def setUp(self):
        self.template_manager = TemplateManager()

    def test_render_default_template(self):
        """Test rendering default template."""
        result = self.template_manager.render_template("default", "Hello")
        # Should return the content as-is for default template
        self.assertEqual(result, "Hello")

    def test_render_translate_template(self):
        """Test rendering translate template."""
        result = self.template_manager.render_template("translate_es", "Hello")
        self.assertIn("Hello", result)
        self.assertIn("Spanish", result)

    def test_missing_template(self):
        """Test handling of missing template."""
        result = self.template_manager.render_template("nonexistent", "Hello")
        # Should fallback to content as-is
        self.assertEqual(result, "Hello")


class TestConfig(unittest.TestCase):
    def test_config_structure(self):
        """Test config dataclass structure."""
        config = Config(
            hotkey_send="ctrl+alt+enter",
            hotkey_cancel="ctrl+alt+backspace",
            hotkey_list_models="ctrl+alt+f8",
            hotkey_diagnostics="ctrl+alt+f9",
            hotkey_template_default="ctrl+alt+1",
            hotkey_template_translate="ctrl+alt+2",
            autopaste=True,
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
        self.assertEqual(config.model, "test_model")
        self.assertEqual(config.min_cps, 6)
        self.assertEqual(config.max_cps, 12)
        self.assertTrue(config.autopaste)


class TestHotkeyManager(unittest.TestCase):
    def setUp(self):
        self.hotkey_manager = HotkeyManager()

    def test_parse_hotkey(self):
        """Test hotkey parsing."""
        # Test various hotkey formats
        result = self.hotkey_manager._parse_hotkey("ctrl+alt+enter")
        self.assertEqual(result, "<ctrl>+<alt>+<enter>")
        
        result = self.hotkey_manager._parse_hotkey("ctrl+alt+f8")
        self.assertEqual(result, "<ctrl>+<alt>+<f8>")
        
        result = self.hotkey_manager._parse_hotkey("ctrl+alt+backspace")
        self.assertEqual(result, "<ctrl>+<alt>+<backspace>")

    def test_register_hotkey(self):
        """Test hotkey registration."""
        callback = Mock()
        self.hotkey_manager.register("ctrl+alt+test", callback)
        
        # Check that hotkey was registered
        self.assertIn("<ctrl>+<alt>+<test>", self.hotkey_manager.hotkeys)


class TestGroqClient(unittest.TestCase):
    def setUp(self):
        self.config = Config(
            hotkey_send="ctrl+alt+enter",
            hotkey_cancel="ctrl+alt+backspace", 
            hotkey_list_models="ctrl+alt+f8",
            hotkey_diagnostics="ctrl+alt+f9",
            hotkey_template_default="ctrl+alt+1",
            hotkey_template_translate="ctrl+alt+2",
            autopaste=True,
            min_cps=6,
            max_cps=12,
            jitter_ms=60,
            punct_pause_ms=220,
            newline_pause_ms=150,
            preserve_clipboard=True,
            timeout_seconds=30,
            max_retries=3,
            blocked_patterns=["sk-", "password="],
            api_base="https://api.groq.com/openai/v1",
            api_key="test_key",
            model="llama-3.1-8b-instant"
        )
        self.client = GroqClient(self.config)

    @patch('httpx.AsyncClient')
    async def test_list_models_success(self, mock_client):
        """Test successful model listing."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"id": "llama-3.1-8b-instant"},
                {"id": "llama-3.1-70b-versatile"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
        
        models = await self.client.list_models()
        self.assertEqual(len(models), 2)
        self.assertIn("llama-3.1-8b-instant", models)

    @patch('httpx.AsyncClient')
    async def test_complete_success(self, mock_client):
        """Test successful completion."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "Hello! How can I help you?"}}
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
        
        response = await self.client.complete("Hello")
        self.assertEqual(response, "Hello! How can I help you?")


class TestIntegration(unittest.TestCase):
    """Integration tests for end-to-end functionality."""
    
    def test_privacy_integration(self):
        """Test privacy filter integration."""
        config = Config(
            hotkey_send="ctrl+alt+enter",
            hotkey_cancel="ctrl+alt+backspace",
            hotkey_list_models="ctrl+alt+f8", 
            hotkey_diagnostics="ctrl+alt+f9",
            hotkey_template_default="ctrl+alt+1",
            hotkey_template_translate="ctrl+alt+2",
            autopaste=True,
            min_cps=6,
            max_cps=12,
            jitter_ms=60,
            punct_pause_ms=220,
            newline_pause_ms=150,
            preserve_clipboard=True,
            timeout_seconds=30,
            max_retries=3,
            blocked_patterns=[
                r"sk-[A-Za-z0-9]{20,}",
                r"password\s*=\s*\S+"
            ],
            api_base="https://api.groq.com/openai/v1",
            api_key="test_key",
            model="llama-3.1-8b-instant"
        )
        
        # Test that sensitive content is blocked
        sensitive_text = "Here's my API key: sk-12345678901234567890abc"
        self.assertTrue(is_blocked(sensitive_text, config.blocked_patterns))
        
        # Test that normal content is not blocked
        normal_text = "Please help me write a professional email"
        self.assertFalse(is_blocked(normal_text, config.blocked_patterns))


async def run_async_tests():
    """Run async tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add async test methods
    suite.addTest(TestGroqClient('test_list_models_success'))
    suite.addTest(TestGroqClient('test_complete_success'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run each async test
    for test in suite:
        if hasattr(test, '_testMethodName'):
            method = getattr(test, test._testMethodName)
            if asyncio.iscoroutinefunction(method):
                try:
                    await method()
                    print(f"✓ {test._testMethodName} passed")
                except Exception as e:
                    print(f"✗ {test._testMethodName} failed: {e}")


if __name__ == '__main__':
    # Run synchronous tests
    print("Running synchronous tests...")
    unittest.main(verbosity=2, exit=False)
    
    # Run asynchronous tests
    print("\nRunning asynchronous tests...")
    asyncio.run(run_async_tests())