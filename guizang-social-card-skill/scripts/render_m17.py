"""
M17 Legal Briefing Pipeline — 自动化渲染脚本
用法: python render_m17.py <项目目录>
从 index.html 渲染所有 .poster.xhs 卡片为 PNG
"""
from playwright.sync_api import sync_playwright
import os, sys, time, glob

CHROME_PATH = r"C:/Program Files/Google/Chrome/Application/chrome.exe"

def render(project_dir):
    html_path = os.path.join(project_dir, "index.html")
    if not os.path.exists(html_path):
        print(f"ERROR: {html_path} not found")
        sys.exit(1)

    file_url = f"file:///{html_path.replace(os.sep, '/')}"
    print(f"Loading: {file_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        page = browser.new_page(viewport={"width": 1920, "height": 1440})
        page.goto(file_url, wait_until="networkidle", timeout=30000)
        time.sleep(3)

        posters = page.query_selector_all(".poster.xhs")
        print(f"Found {len(posters)} .poster.xhs elements")

        for i, poster in enumerate(posters, 1):
            poster_id = poster.get_attribute("id") or f"xhs-{i:02d}"
            out_path = os.path.join(project_dir, f"{poster_id}.png")
            poster.screenshot(path=out_path, type="png", omit_background=True)
            print(f"  [{i}/{len(posters)}] {poster_id}.png")

        browser.close()
    print("Done.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        render(sys.argv[1])
    else:
        print("Usage: python render_m17.py <project_dir>")
