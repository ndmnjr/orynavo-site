"""Browser-level layout checks and screenshots for the local Orynavo site."""
from __future__ import annotations

import base64
import sys
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

ROOT = Path(__file__).parent.resolve()
OUT = ROOT / "screenshots"
BASE_URL = "http://127.0.0.1:4173/"
PAGES = (("home", ""), ("privacy", "privacy.html"), ("404", "404.html"), ("photonbid", "photonbid/"))
VIEWPORTS = (("desktop", 1440, 1000), ("mobile-390", 390, 844))


def driver_for(width: int, height: int) -> webdriver.Chrome:
    options = Options()
    options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    options.add_argument("--headless=new")
    options.add_argument(f"--window-size={width},{height}")
    options.add_argument("--force-device-scale-factor=1")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    return webdriver.Chrome(options=options)


def main() -> int:
    OUT.mkdir(exist_ok=True)
    failures: list[str] = []
    for page_name, path in PAGES:
        for viewport_name, width, height in VIEWPORTS:
            name = f"{page_name}-{viewport_name}"
            driver = driver_for(width, height)
            try:
                driver.execute_cdp_cmd(
                    "Emulation.setDeviceMetricsOverride",
                    {
                        "width": width,
                        "height": height,
                        "deviceScaleFactor": 1,
                        "mobile": width < 500,
                        "screenWidth": width,
                        "screenHeight": height,
                    },
                )
                driver.get(BASE_URL + path)
                actual_width = driver.execute_script("return window.innerWidth")
                scroll_width = driver.execute_script("return document.documentElement.scrollWidth")
                client_width = driver.execute_script("return document.documentElement.clientWidth")
                title = driver.title
                h1 = driver.find_element("css selector", "h1").text
                full_height = driver.execute_script("return document.documentElement.scrollHeight")
                screenshot = OUT / f"{name}.png"
                image = driver.execute_cdp_cmd(
                    "Page.captureScreenshot",
                    {"format": "png", "captureBeyondViewport": True, "fromSurface": True},
                )
                screenshot.write_bytes(base64.b64decode(image["data"]))
                overflow = scroll_width > client_width
                console_errors = [
                    entry for entry in driver.get_log("browser")
                    if entry["level"] == "SEVERE"
                ]
                video_ok = True
                video_detail = ""
                if page_name == "photonbid":
                    video = driver.find_element("css selector", "video")
                    video_state = driver.execute_script(
                        """const v = arguments[0]; return {
                            paused: v.paused,
                            autoplay: v.autoplay,
                            preload: v.preload,
                            readyState: v.readyState,
                            duration: v.duration,
                            tracks: v.textTracks.length,
                            source: v.currentSrc
                        };""",
                        video,
                    )
                    video_ok = (
                        video_state["paused"]
                        and not video_state["autoplay"]
                        and video_state["preload"] == "metadata"
                        and video_state["readyState"] >= 1
                        and 61 <= video_state["duration"] <= 62
                        and video_state["tracks"] == 1
                        and video_state["source"].startswith(BASE_URL)
                    )
                    video_detail = f" video={video_state}"
                ok = actual_width == width and not overflow and bool(h1) and "Orynavo" in title and not console_errors and video_ok
                print(
                    f"{'PASS' if ok else 'FAIL'}: {name} "
                    f"viewport={actual_width} clientWidth={client_width} scrollWidth={scroll_width} "
                    f"height={full_height} overflow={overflow} consoleErrors={len(console_errors)} "
                    f"screenshot={screenshot}{video_detail}"
                )
                for error in console_errors:
                    print(f"  CONSOLE: {error['message']}")
                if not ok:
                    failures.append(name)
            finally:
                driver.quit()
    print(f"SUMMARY: {len(failures)} browser layout failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
