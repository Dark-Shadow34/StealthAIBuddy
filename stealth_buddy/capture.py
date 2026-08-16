import io
import base64
from typing import Tuple, Optional
import mss
from PIL import Image

class ScreenCaptureEngine:
    def __init__(self):
        self._sct = mss.mss()

    def get_monitors(self):
        """Returns list of available monitors info."""
        return self._sct.monitors

    def capture(self, monitor_index: int = 0) -> Image.Image:
        """
        Captures the specified monitor.
        monitor_index 0 = primary monitor (monitors[1] in mss),
        -1 = all monitors combined (monitors[0] in mss).
        """
        try:
            monitors = self._sct.monitors
            if monitor_index == -1:
                target_mon = monitors[0]  # All monitors combined
            elif 0 <= monitor_index < len(monitors) - 1:
                target_mon = monitors[monitor_index + 1]  # 1-indexed in mss
            else:
                target_mon = monitors[1] if len(monitors) > 1 else monitors[0]

            sct_img = self._sct.grab(target_mon)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            return img
        except Exception as e:
            print(f"[Capture] MSS capture error: {e}, falling back to PIL")
            from PIL import ImageGrab
            return ImageGrab.grab(all_screens=(monitor_index == -1))

    def capture_optimized_bytes(
        self,
        monitor_index: int = 0,
        max_dim: int = 1920,
        quality: int = 85,
        img_format: str = "JPEG"
    ) -> Tuple[bytes, str, Tuple[int, int]]:
        """
        Captures screen, resizes if needed, and returns (raw_bytes, base64_str, (width, height)).
        """
        img = self.capture(monitor_index)
        w, h = img.size

        # Downscale proportionally if larger than max_dim to keep payload lightweight & fast
        if max(w, h) > max_dim:
            if w > h:
                new_w = max_dim
                new_h = int(h * (max_dim / w))
            else:
                new_h = max_dim
                new_w = int(w * (max_dim / h))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            w, h = new_w, new_h

        buffer = io.BytesIO()
        if img_format.upper() == "JPEG":
            img.convert("RGB").save(buffer, format="JPEG", quality=quality, optimize=True)
        else:
            img.save(buffer, format="PNG", optimize=True)

        raw_bytes = buffer.getvalue()
        b64_str = base64.b64encode(raw_bytes).decode("utf-8")
        return raw_bytes, b64_str, (w, h)
