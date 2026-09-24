"""Browser-level layout checks and screenshots for the local Orynavo site."""
from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

ROOT = Path(__file__).parent.resolve()
OUT = ROOT / "screenshots"
BASE_URL = os.environ.get("ORYNAVO_BASE_URL", "http://127.0.0.1:4173/")
if not BASE_URL.endswith("/"):
    BASE_URL += "/"
PAGES = (("home", ""), ("privacy", "privacy.html"), ("404", "404.html"), ("photonbid", "photonbid/"))
VIEWPORTS = (
    ("desktop", 1440, 1000),
    ("tablet-768", 768, 1024),
    ("mobile-390", 390, 844),
    ("mobile-320", 320, 720),
)


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
                driver.execute_cdp_cmd(
                    "Emulation.setEmulatedMedia",
                    {"features": [{"name": "prefers-reduced-motion", "value": "reduce"}]},
                )
                driver.get(BASE_URL + path)
                actual_width = driver.execute_script("return window.innerWidth")
                scroll_width = driver.execute_script("return document.documentElement.scrollWidth")
                client_width = driver.execute_script("return document.documentElement.clientWidth")
                title = driver.title
                h1 = driver.find_element("css selector", "h1").text
                full_height = driver.execute_script("return document.documentElement.scrollHeight")
                hidden_reveals = driver.execute_script(
                    "return [...document.querySelectorAll('[data-reveal]')].filter(el => getComputedStyle(el).opacity === '0').length"
                )
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
                small_targets = driver.execute_script(
                    """return [...document.querySelectorAll('a, button, input, select, textarea')]
                    .filter(el => {
                        const r = el.getBoundingClientRect();
                        const s = getComputedStyle(el);
                        const visible = s.display !== 'none' && s.visibility !== 'hidden' &&
                            r.width > 0 && r.height > 0;
                        return visible && (r.width < 44 || r.height < 44);
                    }).map(el => ({tag: el.tagName, text: (el.innerText || el.getAttribute('aria-label') || '').trim(),
                        width: Math.round(el.getBoundingClientRect().width), height: Math.round(el.getBoundingClientRect().height)}));"""
                )
                semantic_ok = page_name != "photonbid" or driver.execute_script(
                    """return document.querySelectorAll('main').length === 1 &&
                        document.querySelectorAll('h1').length === 1 &&
                        !!document.querySelector('a[href="#main"]') &&
                        [...document.images].every(img => img.hasAttribute('alt'));"""
                )
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
                target_ok = page_name != "photonbid" or not small_targets
                ok = actual_width == width and not overflow and bool(h1) and "Orynavo" in title and not console_errors and not hidden_reveals and video_ok and semantic_ok and target_ok
                print(
                    f"{'PASS' if ok else 'FAIL'}: {name} "
                    f"viewport={actual_width} clientWidth={client_width} scrollWidth={scroll_width} "
                    f"height={full_height} overflow={overflow} hiddenReveals={hidden_reveals} consoleErrors={len(console_errors)} "
                    f"semantic={semantic_ok} smallTargets={len(small_targets)} "
                    f"screenshot={screenshot}{video_detail}"
                )
                for error in console_errors:
                    print(f"  CONSOLE: {error['message']}")
                for target in small_targets if page_name == "photonbid" else []:
                    print(f"  TARGET: {target}")
                if not ok:
                    failures.append(name)
            finally:
                driver.quit()
    print(f"SUMMARY: {len(failures)} browser layout failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
