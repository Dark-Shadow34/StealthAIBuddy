import unittest
import os
import sys
from unittest.mock import MagicMock, patch

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stealth_buddy.config import ConfigManager, DEFAULT_CONFIG, PROMPT_PRESETS
from stealth_buddy.capture import ScreenCaptureEngine
from stealth_buddy.ai_engine import AIEngine
from stealth_buddy.hotkey_listener import GlobalHotkeyManager


class TestConfigManager(unittest.TestCase):
    def test_default_config_values(self):
        cfg = ConfigManager("test_config.json")
        self.assertEqual(cfg.get("ai_provider"), "gemini")
        self.assertTrue(cfg.get("stealth_exclude_capture"))
        self.assertEqual(cfg.get("overlay_position"), "top_left")

    def test_set_and_get(self):
        cfg = ConfigManager("test_config.json")
        cfg.set("font_size", 14)
        self.assertEqual(cfg.get("font_size"), 14)

    def test_prompt_presets(self):
        cfg = ConfigManager("test_config.json")
        cfg.set("prompt_preset", "direct_answer")
        prompt = cfg.get_system_prompt()
        self.assertIn("StealthAI Buddy", prompt)


class TestScreenCaptureEngine(unittest.TestCase):
    def test_capture_and_optimize(self):
        engine = ScreenCaptureEngine()
        raw_bytes, b64_str, (w, h) = engine.capture_optimized_bytes(monitor_index=0, max_dim=800)
        self.assertGreater(len(raw_bytes), 0)
        self.assertGreater(len(b64_str), 0)
        self.assertLessEqual(max(w, h), 800)


class TestAIEngine(unittest.TestCase):
    def setUp(self):
        self.cfg = ConfigManager("test_config.json")
        self.engine = AIEngine(self.cfg)

    @patch("requests.post")
    def test_gemini_api_call(self, mock_post):
        self.cfg.set("ai_provider", "gemini")
        self.cfg.set("gemini_api_key", "test_gemini_key")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "Option C: 42"}]
                    }
                }
            ]
        }
        mock_post.return_value = mock_resp

        success, answer = self.engine.analyze_screen("fake_b64_image")
        self.assertTrue(success)
        self.assertEqual(answer, "Option C: 42")

    @patch("requests.post")
    def test_openai_api_call(self, mock_post):
        self.cfg.set("ai_provider", "openai")
        self.cfg.set("openai_api_key", "sk-test")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "The derivative is 2x + 3."
                    }
                }
            ]
        }
        mock_post.return_value = mock_resp

        success, answer = self.engine.analyze_screen("fake_b64_image")
        self.assertTrue(success)
        self.assertEqual(answer, "The derivative is 2x + 3.")

    def test_missing_api_key(self):
        self.cfg.set("ai_provider", "gemini")
        self.cfg.set("gemini_api_key", "")
        success, answer = self.engine.analyze_screen("fake_b64_image")
        self.assertFalse(success)
        self.assertIn("API Key missing", answer)


if __name__ == "__main__":
    unittest.main()
