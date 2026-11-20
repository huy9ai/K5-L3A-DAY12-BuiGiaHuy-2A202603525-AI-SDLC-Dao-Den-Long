"""Capture real 1280x720 WebGL2 gameplay preview PNG (docs/demo/preview.png) and H.264 MP4 video (docs/demo/demo.mp4)
directly from Google Chrome rendering the live 3D WebGL2 game (`/?mode=record_demo`)."""

from __future__ import annotations

import base64
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dao_den_long.web.server import create_server  # noqa: E402


def _find_chrome() -> str | None:
    candidates = [
        shutil.which("google-chrome"),
        shutil.which("chrome"),
        shutil.which("chromium"),
        shutil.which("msedge"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None


def main() -> int:
    browser_bin = _find_chrome()
    if not browser_bin:
        print("Error: Chrome/Edge binary not found.", file=sys.stderr)
        return 1

    demo_dir = ROOT_DIR / "docs" / "demo"
    demo_dir.mkdir(parents=True, exist_ok=True)
    preview_path = demo_dir / "preview.png"
    mp4_path = demo_dir / "demo.mp4"

    server, port = create_server("127.0.0.1", 0, seed=42, quiet=True)
    srv_thread = threading.Thread(target=server.serve_forever, daemon=True)
    srv_thread.start()

    url = f"http://127.0.0.1:{port}/?mode=record_demo"
    print(f"Launching {browser_bin} -> {url}")

    with tempfile.TemporaryDirectory() as profile_dir:
        cmd = [
            browser_bin,
            "--window-size=1280,760",
            "--no-first-run",
            "--no-default-browser-check",
            "--autoplay-policy=no-user-gesture-required",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            f"--user-data-dir={profile_dir}",
            f"--app={url}",
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            deadline = time.perf_counter() + 45.0
            while time.perf_counter() < deadline:
                if server.session.demo_capture_result is not None:
                    res = server.session.demo_capture_result
                    data_url = str(res.get("preview_data_url") or "")
                    if "," in data_url:
                        png_bytes = base64.b64decode(data_url.split(",", 1)[1])
                        preview_path.write_bytes(png_bytes)

                    vid_b64 = str(res.get("video_base64") or "")
                    if vid_b64:
                        vid_bytes = base64.b64decode(vid_b64)
                        mp4_path.write_bytes(vid_bytes)

                    print(
                        f"Captured real WebGL2 media! mime={res.get('mime_type')} | "
                        f"preview.png={preview_path.stat().st_size} bytes | "
                        f"demo.mp4={mp4_path.stat().st_size} bytes"
                    )
                    return 0
                time.sleep(0.1)
            print("Timed out waiting for Chrome WebGL2 demo capture.", file=sys.stderr)
            return 1
        finally:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                pass
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
