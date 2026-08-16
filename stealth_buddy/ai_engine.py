import json
import base64
from typing import Optional, Tuple, List, Dict
import requests

from .config import ConfigManager, auto_detect_provider

GEMINI_FALLBACK_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash-8b",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
    "gemini-2.0-flash-exp",
]

OPENAI_FALLBACK_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "chatgpt-4o-latest"
]


class AIEngine:
    def __init__(self, config_mgr: ConfigManager):
        self.config = config_mgr

    def auto_discover_gemini_models(self, api_key: str) -> Tuple[bool, List[str], str]:
        """Queries Google Gemini API to discover all available models for this specific key."""
        key = api_key.strip()
        if not key:
            return False, [], "API key is empty."

        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        try:
            resp = requests.get(url, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                models = []
                for m in data.get("models", []):
                    name = m.get("name", "").replace("models/", "")
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        models.append(name)

                # Prioritize working 2025/2026 models first
                priority_order = [
                    "gemini-2.5-flash-lite", "gemini-2.5-flash-8b",
                    "gemini-2.0-flash", "gemini-2.0-flash-lite",
                    "gemini-2.5-flash", "gemini-1.5-flash",
                    "gemini-1.5-pro", "gemini-2.0-flash-exp",
                ]
                sorted_models = []
                for pref in priority_order:
                    if pref in models:
                        sorted_models.append(pref)
                for m in models:
                    if m not in sorted_models and "gemini" in m:
                        # Skip known deprecated/removed models
                        if m not in ("gemini-1.0-pro-vision-latest", "gemini-pro-vision"):
                            sorted_models.append(m)

                if sorted_models:
                    return True, sorted_models, f"Discovered {len(sorted_models)} models."
                return True, GEMINI_FALLBACK_MODELS, "Default model list active."
            elif resp.status_code == 400 or resp.status_code == 403:
                return False, [], "Invalid API Key or API not enabled in Google Cloud/AI Studio (403/400)."
            else:
                return False, [], f"Gemini Error {resp.status_code}: {resp.text[:140]}"
        except Exception as e:
            return False, [], f"Connection error: {str(e)}"

    def test_smart_key(self, api_key: str) -> Tuple[bool, str, str, str]:
        """
        Auto-identifies provider, validates the key against live API,
        and auto-discovers optimal model.
        Returns: (success: bool, provider: str, best_model: str, message: str)
        """
        prov, prov_name = auto_detect_provider(api_key)
        key = api_key.strip()

        if prov == "gemini":
            ok, models, msg = self.auto_discover_gemini_models(key)
            if ok:
                # Try each discovered model until one actually responds (skip 404/deprecated)
                best_model = None
                val_msg = "No models tested yet."
                for candidate in (models if models else GEMINI_FALLBACK_MODELS):
                    val_ok, val_msg = self._test_gemini_key_with_model(key, candidate)
                    if val_ok:
                        best_model = candidate
                        break

                if best_model:
                    self.config.set("ai_provider", "gemini")
                    self.config.set("gemini_api_key", key)
                    self.config.set("gemini_model", best_model)
                    self.config.save()
                    return True, "gemini", best_model, f"✓ Verified Google Gemini Key! Active model: {best_model}"
                else:
                    tried = models[:4] if models else GEMINI_FALLBACK_MODELS[:4]
                    return False, "gemini", "", f"Key is valid but no working model found. Models tried: {tried}. Last error: {val_msg}"
            else:
                return False, "gemini", "gemini-2.0-flash", f"Gemini verification failed: {msg}"

        elif prov == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            payload = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5}
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=12)
                if resp.status_code == 200:
                    self.config.set("ai_provider", "openai")
                    self.config.set("openai_api_key", key)
                    self.config.set("openai_model", "gpt-4o")
                    self.config.save()
                    return True, "openai", "gpt-4o", "✓ Verified OpenAI API Key! (GPT-4o active)"
                elif resp.status_code == 401:
                    return False, "openai", "gpt-4o", "Invalid OpenAI API Key (401 Unauthorized)."
                elif resp.status_code == 429:
                    return False, "openai", "gpt-4o", "OpenAI Quota Exceeded (429 Rate Limit/Billing)."
                return False, "openai", "gpt-4o", f"OpenAI Error {resp.status_code}: {resp.text[:120]}"
            except Exception as e:
                return False, "openai", "gpt-4o", f"OpenAI Connection Failed: {str(e)}"

        elif prov == "claude":
            url = "https://api.anthropic.com/v1/messages"
            headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
            payload = {"model": "claude-3-5-haiku-20241022", "max_tokens": 5, "messages": [{"role": "user", "content": "Hi"}]}
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=12)
                if resp.status_code == 200:
                    self.config.set("ai_provider", "claude")
                    self.config.set("claude_api_key", key)
                    self.config.set("claude_model", "claude-3-5-sonnet-20241022")
                    self.config.save()
                    return True, "claude", "claude-3-5-sonnet-20241022", "✓ Verified Anthropic Claude API Key!"
                return False, "claude", "claude-3-5-sonnet-20241022", f"Claude Error {resp.status_code}: {resp.text[:120]}"
            except Exception as e:
                return False, "claude", "claude-3-5-sonnet-20241022", f"Claude Connection Failed: {str(e)}"

        return False, prov, "", "Unrecognized API key format."

    def _test_gemini_key_with_model(self, api_key: str, model: str) -> Tuple[bool, str]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": "Respond with OK."}]}],
            "generationConfig": {"maxOutputTokens": 10}
        }
        try:
            resp = requests.post(url, json=payload, timeout=12)
            if resp.status_code == 200:
                return True, "Success"
            return False, f"HTTP {resp.status_code}: {resp.text[:120]}"
        except Exception as e:
            return False, str(e)

    def test_connection(self, provider: Optional[str] = None) -> Tuple[bool, str]:
        prov = (provider or self.config.get("ai_provider", "gemini")).lower()
        key = self.config.get_decrypted_key(prov)
        if not key and prov not in ("ollama", "custom"):
            return False, f"{prov.capitalize()} API key is empty."

        ok, _, _, msg = self.test_smart_key(key)
        return ok, msg

    def analyze_screen(self, b64_image: str, custom_instruction: Optional[str] = None) -> Tuple[bool, str]:
        provider = self.config.get("ai_provider", "gemini").lower()
        system_prompt = custom_instruction if custom_instruction else self.config.get_system_prompt()

        try:
            if provider == "gemini":
                return self._call_gemini_with_fallback(b64_image, system_prompt)
            elif provider == "openai":
                return self._call_openai_with_fallback(b64_image, system_prompt)
            elif provider == "claude":
                return self._call_claude(b64_image, system_prompt)
            elif provider == "ollama":
                return self._call_ollama(b64_image, system_prompt)
            elif provider == "custom":
                return self._call_custom(b64_image, system_prompt)
            else:
                return False, f"Unknown AI provider: {provider}"
        except Exception as e:
            return False, f"AI Error ({provider}): {str(e)}"

    def _call_gemini_with_fallback(self, b64_image: str, prompt: str) -> Tuple[bool, str]:
        api_key = self.config.get_decrypted_key("gemini")
        if not api_key:
            return False, "Gemini API Key missing. Please paste your key in Settings (Ctrl+Alt+O)."

        active_model = self.config.get("gemini_model", "gemini-2.0-flash")
        model_queue = [active_model] + [m for m in GEMINI_FALLBACK_MODELS if m != active_model]

        last_error = ""
        for model in model_queue:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

            # Official Google REST payload with inlineData (camelCase)
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt},
                            {
                                "inlineData": {
                                    "mimeType": "image/jpeg",
                                    "data": b64_image
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": float(self.config.get("temperature", 0.15)),
                    "maxOutputTokens": 1024
                }
            }

            try:
                resp = requests.post(url, json=payload, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    try:
                        candidate = data["candidates"][0]
                        text = candidate["content"]["parts"][0]["text"].strip()
                        # If fallback succeeded, update config so future calls use this working model
                        if model != active_model:
                            self.config.set("gemini_model", model)
                            self.config.save()
                        return True, text
                    except (KeyError, IndexError):
                        return False, f"Unexpected response structure from {model}: {str(data)[:200]}"
                elif resp.status_code == 404:
                    last_error = f"Model '{model}' not found (404). Trying next fallback..."
                    continue
                elif resp.status_code == 400:
                    # Try snake_case inline_data fallback for older endpoints
                    payload["contents"][0]["parts"][1] = {
                        "inline_data": {"mime_type": "image/jpeg", "data": b64_image}
                    }
                    resp_alt = requests.post(url, json=payload, timeout=25)
                    if resp_alt.status_code == 200:
                        candidate = resp_alt.json()["candidates"][0]
                        return True, candidate["content"]["parts"][0]["text"].strip()
                    last_error = f"Gemini Error 400 on {model}: {resp.text[:140]}"
                    continue
                elif resp.status_code == 403:
                    return False, "Gemini API Key is invalid or permission denied (403). Please verify in Google AI Studio."
                elif resp.status_code == 429:
                    return False, "Gemini Quota limit exceeded (429). Please check your account quota or upgrade plan."
                else:
                    last_error = f"Gemini Error {resp.status_code} on {model}: {resp.text[:140]}"
            except Exception as e:
                last_error = f"Connection exception on '{model}': {str(e)}"

        return False, f"All Gemini model endpoints failed. Last error: {last_error}"

    def _call_openai_with_fallback(self, b64_image: str, prompt: str) -> Tuple[bool, str]:
        api_key = self.config.get_decrypted_key("openai")
        if not api_key:
            return False, "OpenAI API Key missing. Please paste your key in Settings (Ctrl+Alt+O)."

        active_model = self.config.get("openai_model", "gpt-4o")
        model_queue = [active_model] + [m for m in OPENAI_FALLBACK_MODELS if m != active_model]

        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        for model in model_queue:
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64_image}", "detail": "high"}
                            }
                        ]
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 1024
            }

            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    text = resp.json()["choices"][0]["message"]["content"].strip()
                    return True, text
                elif resp.status_code in (404, 400) and model != model_queue[-1]:
                    continue
                else:
                    return False, f"OpenAI Error {resp.status_code}: {resp.text[:140]}"
            except Exception as e:
                return False, f"OpenAI Exception: {str(e)}"

        return False, "OpenAI request failed on all models."

    def _call_claude(self, b64_image: str, prompt: str) -> Tuple[bool, str]:
        api_key = self.config.get_decrypted_key("claude")
        if not api_key:
            return False, "Anthropic API Key missing. Please paste your key in Settings (Ctrl+Alt+O)."

        model = self.config.get("claude_model", "claude-3-5-sonnet-20241022")
        url = "https://api.anthropic.com/v1/messages"
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        payload = {
            "model": model,
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64_image}},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                return True, resp.json()["content"][0]["text"].strip()
            return False, f"Claude Error {resp.status_code}: {resp.text[:140]}"
        except Exception as e:
            return False, f"Claude Exception: {str(e)}"

    def _call_ollama(self, b64_image: str, prompt: str) -> Tuple[bool, str]:
        base_url = self.config.get("custom_base_url", "http://localhost:11434").rstrip("/")
        model = self.config.get("custom_model", "llava")
        url = f"{base_url}/api/generate"
        payload = {"model": model, "prompt": prompt, "images": [b64_image], "stream": False}
        try:
            resp = requests.post(url, json=payload, timeout=40)
            if resp.status_code == 200:
                return True, resp.json().get("response", "").strip()
        except Exception:
            pass
        return self._call_custom(b64_image, prompt)

    def _call_custom(self, b64_image: str, prompt: str) -> Tuple[bool, str]:
        base_url = self.config.get("custom_base_url", "http://localhost:11434/v1").rstrip("/")
        api_key = self.config.get_decrypted_key("custom") or "none"
        model = self.config.get("custom_model", "llava")

        url = f"{base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                    ]
                }
            ],
            "max_tokens": 1024,
            "temperature": 0.2
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                return True, resp.json()["choices"][0]["message"]["content"].strip()
            return False, f"Custom Endpoint Error {resp.status_code}: {resp.text[:140]}"
        except Exception as e:
            return False, f"Custom Endpoint Exception: {str(e)}"
