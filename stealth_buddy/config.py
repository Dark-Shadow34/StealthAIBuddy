import json
import os
import sys
import base64
import ctypes
from ctypes import wintypes
from pathlib import Path
from typing import Any, Dict, Tuple, Optional

# Win32 DPAPI Encryption structures
class DATA_BLOB(ctypes.Structure):
    _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_char))]

def encrypt_secret(plaintext: str) -> str:
    """Encrypts a string using Windows DPAPI (tied to current user & machine)."""
    if not plaintext or not plaintext.strip():
        return ""
    if sys.platform != "win32":
        return plaintext
    try:
        data_bytes = plaintext.strip().encode("utf-8")
        in_blob = DATA_BLOB(
            len(data_bytes),
            ctypes.cast(ctypes.create_string_buffer(data_bytes), ctypes.POINTER(ctypes.c_char))
        )
        out_blob = DATA_BLOB()
        if ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(in_blob), "StealthAISecureKey", None, None, None, 0, ctypes.byref(out_blob)
        ):
            res = ctypes.string_at(out_blob.pbData, out_blob.cbData)
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)
            return "DPAPI:" + base64.b64encode(res).decode("utf-8")
    except Exception as e:
        print(f"[Crypto] Encryption fallback: {e}")
    return plaintext

def decrypt_secret(encrypted_str: str) -> str:
    """Decrypts a DPAPI-encrypted string."""
    if not encrypted_str:
        return ""
    if not encrypted_str.startswith("DPAPI:"):
        return encrypted_str
    if sys.platform != "win32":
        return encrypted_str
    try:
        raw_bytes = base64.b64decode(encrypted_str[6:])
        in_blob = DATA_BLOB(
            len(raw_bytes),
            ctypes.cast(ctypes.create_string_buffer(raw_bytes), ctypes.POINTER(ctypes.c_char))
        )
        out_blob = DATA_BLOB()
        if ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)
        ):
            res = ctypes.string_at(out_blob.pbData, out_blob.cbData)
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)
            return res.decode("utf-8")
    except Exception as e:
        print(f"[Crypto] Decryption fallback: {e}")
    return encrypted_str


def auto_detect_provider(api_key: str) -> Tuple[str, str]:
    """Auto-detects AI provider from the API key format."""
    key = api_key.strip()
    if key.startswith("AIzaSy") or (key.startswith("AIza") and len(key) >= 28):
        return "gemini", "Google Gemini"
    elif key.startswith("sk-ant-"):
        return "claude", "Anthropic Claude"
    elif key.startswith("sk-or-"):
        return "custom", "OpenRouter"
    elif key.startswith("gsk_"):
        return "custom", "Groq"
    elif key.startswith("sk-proj-") or key.startswith("sk-"):
        return "openai", "OpenAI"
    elif key.startswith("http://") or key.startswith("https://") or "localhost" in key:
        return "ollama", "Local / Ollama"
    return "gemini", "Google Gemini"


HUD_THEMES: Dict[str, Dict[str, Any]] = {
    "midnight_obsidian": {
        "name": "Midnight Obsidian",
        "desc": "Obsidian glass with electric indigo accents",
        "card_bg": "rgba(8, 9, 14, 0.94)",
        "border": "rgba(255, 255, 255, 0.08)",
        "hover_border": "rgba(99, 102, 241, 0.45)",
        "accent": "#6366f1",
        "accent_hover": "#818cf8",
        "text_color": "#f1f5f9",
        "muted_color": "#6b7280",
        "code_bg": "rgba(15, 23, 42, 0.85)",
        "code_border": "#6366f1",
        "shadow_rgba": (0, 0, 0, 220),
    },
    "cyber_emerald": {
        "name": "Matrix Emerald",
        "desc": "Phosphorescent emerald terminal HUD",
        "card_bg": "rgba(5, 14, 10, 0.94)",
        "border": "rgba(16, 229, 153, 0.22)",
        "hover_border": "rgba(16, 229, 153, 0.60)",
        "accent": "#10e599",
        "accent_hover": "#34d399",
        "text_color": "#e8fff5",
        "muted_color": "#34d399",
        "code_bg": "rgba(6, 24, 16, 0.9)",
        "code_border": "#10e599",
        "shadow_rgba": (0, 20, 10, 220),
    },
    "cyberpunk_neon": {
        "name": "Cyberpunk Neon",
        "desc": "Violet glass with electric neon rose and cyan",
        "card_bg": "rgba(13, 8, 20, 0.94)",
        "border": "rgba(244, 63, 94, 0.25)",
        "hover_border": "rgba(56, 189, 248, 0.60)",
        "accent": "#f43f5e",
        "accent_hover": "#fb7185",
        "text_color": "#fdf2f8",
        "muted_color": "#f472b6",
        "code_bg": "rgba(24, 12, 38, 0.9)",
        "code_border": "#f43f5e",
        "shadow_rgba": (20, 0, 25, 220),
    },
    "minimal_ghost": {
        "name": "Minimal Ghost",
        "desc": "Ultra-light borderless text with ambient shadow",
        "card_bg": "rgba(0, 0, 0, 0.18)",
        "border": "rgba(255, 255, 255, 0.05)",
        "hover_border": "rgba(255, 255, 255, 0.28)",
        "accent": "#ffffff",
        "accent_hover": "#e2e8f0",
        "text_color": "#ffffff",
        "muted_color": "#94a3b8",
        "code_bg": "rgba(0, 0, 0, 0.65)",
        "code_border": "#ffffff",
        "shadow_rgba": (0, 0, 0, 240),
    },
    "solar_amber": {
        "name": "Solar Amber",
        "desc": "Warm luxury charcoal with glowing gold",
        "card_bg": "rgba(15, 11, 6, 0.94)",
        "border": "rgba(245, 158, 11, 0.22)",
        "hover_border": "rgba(245, 158, 11, 0.60)",
        "accent": "#f59e0b",
        "accent_hover": "#fbbf24",
        "text_color": "#fffbeb",
        "muted_color": "#d97706",
        "code_bg": "rgba(28, 19, 8, 0.9)",
        "code_border": "#f59e0b",
        "shadow_rgba": (20, 12, 0, 220),
    },
    "nordic_frost": {
        "name": "Nordic Frost",
        "desc": "Frosted titanium slate with ice cyan glow",
        "card_bg": "rgba(10, 15, 22, 0.94)",
        "border": "rgba(56, 189, 248, 0.22)",
        "hover_border": "rgba(56, 189, 248, 0.60)",
        "accent": "#38bdf8",
        "accent_hover": "#7dd3fc",
        "text_color": "#f0f9ff",
        "muted_color": "#38bdf8",
        "code_bg": "rgba(12, 25, 38, 0.9)",
        "code_border": "#38bdf8",
        "shadow_rgba": (0, 15, 25, 220),
    },
    "tactical_crimson": {
        "name": "Tactical Crimson",
        "desc": "Stealth red night-vision high contrast",
        "card_bg": "rgba(18, 6, 6, 0.94)",
        "border": "rgba(239, 68, 68, 0.25)",
        "hover_border": "rgba(239, 68, 68, 0.65)",
        "accent": "#ef4444",
        "accent_hover": "#f87171",
        "text_color": "#fef2f2",
        "muted_color": "#f87171",
        "code_bg": "rgba(36, 10, 10, 0.9)",
        "code_border": "#ef4444",
        "shadow_rgba": (25, 0, 0, 220),
    },
}

DEFAULT_CONFIG: Dict[str, Any] = {
    # AI Backend Settings
    "ai_provider": "gemini",  # gemini, openai, claude, ollama, custom
    "gemini_api_key": "",
    "openai_api_key": "",
    "claude_api_key": "",
    "custom_api_key": "",
    "custom_base_url": "http://localhost:11434/v1",
    
    # Models
    "gemini_model": "gemini-2.0-flash",
    "openai_model": "gpt-4o",
    "claude_model": "claude-3-5-sonnet-20241022",
    "custom_model": "llava",
    
    # Prompts & Modes
    "prompt_preset": "direct_answer",
    "custom_system_prompt": "",
    "temperature": 0.2,
    
    # Global Hotkeys
    "hotkey_scan": "ctrl+alt+s",
    "hotkey_quick_scan": "f9",
    "hotkey_panic": "esc",
    "hotkey_settings": "ctrl+alt+o",
    "hotkey_repeat": "ctrl+alt+r",
    
    # Overlay Appearance & Luxury Styling
    "hud_theme": "midnight_obsidian",
    "overlay_opacity": 0.90,
    "hover_dimming": True,
    "idle_opacity": 0.45,
    "enable_animations": True,
    "font_size": 11,
    "font_family": "Segoe UI",
    "text_color": "#f1f5f9",
    "accent_color": "#6366f1",
    "bg_style": "dark_glass",
    "overlay_position": "top_left",
    "custom_pos_x": 16,
    "custom_pos_y": 16,
    "max_width": 390,
    "max_height": 480,
    "compact_mode": False,
    
    # Stealth & Disguise Settings
    "stealth_exclude_capture": True,
    "click_through": False,
    "simple_stealth_mode": False,
    "simple_mode_width": 380,
    "simple_mode_height": 260,
    "simple_mode_x": 30,
    "simple_mode_y": 30,
    "tray_mode": "discreet",
    "auto_hide_seconds": 0,
    "monitor_index": 0,
    "autostart": False,
    "auto_copy_clipboard": False,
    "sound_alert": False,
    "capture_quality": "balanced",
    "capture_delay_ms": 0,
    "window_title_mask": "",
    "alttab_hide": False,
    "taskbar_hide": True,
}

PROMPT_PRESETS = {
    "direct_answer": (
        "You are StealthAI Buddy, a high-precision, low-profile desktop assistant.\n"
        "Look at this screenshot immediately. Identify the primary question, task, or problem shown.\n"
        "Give the DIRECT, ACCURATE answer first in clear plain text.\n"
        "If it is a multiple-choice question, state the exact option letter and text first.\n"
        "Follow with a brief 1-2 sentence explanation or key formula/code snippet only if helpful.\n"
        "Keep the output compact, plain text, and easy to read quickly at a glance."
    ),
    "concise_solution": (
        "You are StealthAI Buddy. Analyze this screen capture.\n"
        "Detect any question, math problem, or challenge.\n"
        "Provide: 1) Final Answer, 2) Key Steps / Reasoning in 2-3 bullet points.\n"
        "Be extremely concise, clear, and direct."
    ),
    "code_only": (
        "You are StealthAI Buddy. Analyze the coding problem or challenge on screen.\n"
        "Provide the optimal, working code solution directly. Include minimal comments only for key logic.\n"
        "Do not include long conversational fluff."
    ),
    "multiple_choice": (
        "You are StealthAI Buddy. Analyze the quiz or test question on screen.\n"
        "1. Identify the question.\n"
        "2. State the CORRECT OPTION directly (e.g. 'Option B: ...').\n"
        "3. Provide a 1-sentence justification why it is correct."
    ),
    "step_by_step": (
        "You are StealthAI Buddy. Analyze the problem or task shown on screen.\n"
        "Provide the final answer first, followed by clear numbered step-by-step instructions or derivations."
    ),
}

SECRET_KEYS = ["gemini_api_key", "openai_api_key", "claude_api_key", "custom_api_key"]


class ConfigManager:
    def __init__(self, config_file: str = "config.json"):
        self.config_dir = Path(os.environ.get("APPDATA", ".")) / "StealthAIBuddy"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.config_dir / config_file
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        cfg = DEFAULT_CONFIG.copy()
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    cfg.update(loaded)
            except Exception as e:
                print(f"[Config] Error loading config: {e}")
        return cfg

    def save(self) -> bool:
        try:
            # Create a copy with encrypted keys for disk storage
            disk_data = self.data.copy()
            for k in SECRET_KEYS:
                raw = str(disk_data.get(k, "")).strip()
                if raw and not raw.startswith("DPAPI:"):
                    disk_data[k] = encrypt_secret(raw)

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(disk_data, f, indent=2)
            return True
        except Exception as e:
            print(f"[Config] Error saving config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        val = self.data.get(key, default if default is not None else DEFAULT_CONFIG.get(key))
        if key in SECRET_KEYS and isinstance(val, str) and val.startswith("DPAPI:"):
            return decrypt_secret(val)
        return val

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def get_decrypted_key(self, provider: Optional[str] = None) -> str:
        """Returns the decrypted API key for the given provider. config.get() already handles DPAPI transparently."""
        prov = provider or self.get("ai_provider", "gemini")
        field = f"{prov}_api_key"
        return str(self.get(field, "")).strip()

    def set_smart_key(self, api_key: str) -> Tuple[str, str]:
        """Auto-detects provider from key, sets it, and saves."""
        prov, prov_name = auto_detect_provider(api_key)
        self.set("ai_provider", prov)
        self.set(f"{prov}_api_key", api_key.strip())
        self.save()
        return prov, prov_name

    def get_system_prompt(self) -> str:
        preset = self.get("prompt_preset", "direct_answer")
        if preset == "custom":
            custom = self.get("custom_system_prompt", "").strip()
            return custom if custom else PROMPT_PRESETS["direct_answer"]
        return PROMPT_PRESETS.get(preset, PROMPT_PRESETS["direct_answer"])
