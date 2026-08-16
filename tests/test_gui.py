import unittest
import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stealth_buddy.config import ConfigManager, HUD_THEMES
from stealth_buddy.overlay import StealthOverlayHUD
from stealth_buddy.settings_gui import SettingsDialog, ModernSwitch, SlidingStackedWidget


class TestQtComponents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def test_modern_switch(self):
        switch = ModernSwitch(checked=False)
        self.assertFalse(switch.isChecked())
        
        toggled_vals = []
        switch.toggled.connect(lambda v: toggled_vals.append(v))
        
        switch.setChecked(True, animate=False)
        self.assertTrue(switch.isChecked())
        self.assertEqual(switch.get_thumb_pos(), 1.0)
        self.assertEqual(toggled_vals, [True])

        switch.toggle()
        self.assertFalse(switch.isChecked())
        self.assertEqual(toggled_vals, [True, False])

    def test_sliding_stacked_widget(self):
        stack = SlidingStackedWidget()
        w1 = stack.addWidget(ModernSwitch())
        w2 = stack.addWidget(ModernSwitch())
        self.assertEqual(stack.count(), 2)
        stack.setCurrentIndex(0)
        self.assertEqual(stack.currentIndex(), 0)

    def test_overlay_themes_and_config(self):
        cfg = ConfigManager("test_qt_config.json")
        cfg.set("overlay_opacity", 0.85)
        cfg.set("enable_animations", False)
        cfg.set("hud_theme", "cyber_emerald")
        overlay = StealthOverlayHUD(cfg)

        self.assertAlmostEqual(overlay.windowOpacity(), 0.85, places=2)
        overlay.show_status("Ready", "#10e599")
        self.assertIn("READY", overlay.status_label.text())

        overlay.set_content("**Option A: Correct Answer**\n\n```python\nprint('hello')\n```")
        self.assertIn("Option A: Correct Answer", overlay.text_area.toPlainText())
        overlay.hide_overlay()
        self.assertFalse(overlay.isVisible())

    def test_settings_dialog_tabs_and_save(self):
        cfg = ConfigManager("test_qt_config.json")
        dlg = SettingsDialog(cfg)
        self.assertIsNotNone(dlg)
        
        # Test tab switches
        for i in range(5):
            dlg._switch_tab(i)
            self.assertEqual(dlg._current_tab, i)

        # Test theme switch
        dlg._select_theme("cyberpunk_neon")
        self.assertEqual(dlg._active_theme_key, "cyberpunk_neon")

        # Test toggles
        dlg.switch_auto_copy.setChecked(True, animate=False)
        self.assertTrue(dlg.switch_auto_copy.isChecked())

        dlg._on_save_clicked()
        self.assertEqual(cfg.get("hud_theme"), "cyberpunk_neon")
        self.assertTrue(cfg.get("auto_copy_clipboard"))
        dlg.close()


if __name__ == "__main__":
    unittest.main()
