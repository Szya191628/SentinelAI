"""
Cookie 获取工具
用 Edge 打开目标平台，手动登录后自动保存 Cookie。
"""
import asyncio
import json
import sys
from pathlib import Path

PLATFORMS = {
    "xhs": "https://www.xiaohongshu.com",
    "dy": "https://www.douyin.com",
    "wb": "https://weibo.com",
    "bili": "https://www.bilibili.com",
    "ks": "https://www.kuaishou.com",
    "zhihu": "https://www.zhihu.com",
    "tieba": "https://tieba.baidu.com",
}

COOKIE_DIR = Path(__file__).parent / "cookies"
COOKIE_DIR.mkdir(exist_ok=True)


async def get_cookie(platform: str):
    if platform not in PLATFORMS:
        print(f"Unknown platform: {platform}")
        print(f"Supported: {', '.join(PLATFORMS.keys())}")
        return

    url = PLATFORMS[platform]
    print(f"\n{'='*50}")
    print(f"  Platform: {platform}")
    print(f"  URL: {url}")
    print(f"{'='*50}")
    print()
    print("Edge browser will open. Please log in manually.")
    print("After login, come back here and press ENTER to save cookies.")
    print()

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="msedge",
            headless=False,
            args=["--start-maximized"],
        )
        context = await browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
        )
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded")

        input(">>> Press ENTER after you have logged in...")

        cookies = await context.cookies()
        cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

        # Save to file
        save_path = COOKIE_DIR / f"{platform}_cookies.txt"
        save_path.write_text(cookie_str, encoding="utf-8")

        # Also save as JSON for reference
        json_path = COOKIE_DIR / f"{platform}_cookies.json"
        json_path.write_text(json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"\nSaved {len(cookies)} cookies to:")
        print(f"  {save_path}")
        print(f"  {json_path}")
        print(f"\nCookie string (first 100 chars): {cookie_str[:100]}...")

        await browser.close()


def load_cookie(platform: str) -> str:
    """Load saved cookie string for a platform."""
    path = COOKIE_DIR / f"{platform}_cookies.txt"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


async def main():
    if len(sys.argv) < 2:
        print("Usage: python get_cookies.py <platform>")
        print(f"Platforms: {', '.join(PLATFORMS.keys())}")
        print(f"\nExample: python get_cookies.py xhs")
        return

    platform = sys.argv[1].lower()
    await get_cookie(platform)


if __name__ == "__main__":
    asyncio.run(main())
