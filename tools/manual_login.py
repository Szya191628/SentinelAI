"""
手动登录工具
打开 Edge 浏览器，让你手动登录，然后自动保存 Cookie 供爬虫使用。
用法: python manual_login.py <platform>
平台: wb, ks, xhs, dy, bili, zhihu, tieba
"""
import asyncio
import json
import sys
import os

PLATFORMS = {
    "xhs": "https://www.xiaohongshu.com",
    "dy": "https://www.douyin.com",
    "wb": "https://weibo.com",
    "bili": "https://www.bilibili.com",
    "ks": "https://www.kuaishou.com",
    "zhihu": "https://www.zhihu.com",
    "tieba": "https://tieba.baidu.com",
}

BROWSER_DATA_DIR = os.path.join(os.path.dirname(__file__),
    "SentinelSpider/DeepSentimentCrawling/MediaCrawler/browser_data")


async def manual_login(platform: str):
    if platform not in PLATFORMS:
        print(f"Unknown platform: {platform}")
        print(f"Supported: {', '.join(PLATFORMS.keys())}")
        return

    url = PLATFORMS[platform]
    user_data_dir = os.path.join(BROWSER_DATA_DIR, f"{platform}_user_data_dir")

    print(f"\n{'='*50}")
    print(f"  Platform: {platform}")
    print(f"  URL: {url}")
    print(f"  Data: {user_data_dir}")
    print(f"{'='*50}")
    print()
    print("Edge will open. Please log in manually.")
    print("After login, press Ctrl+C here to save and exit.")
    print()

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        # 使用持久化上下文，和爬虫用同一个 user_data_dir
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="msedge",
            headless=False,
            args=["--start-maximized"],
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
        )

        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded")

        print("Browser opened. Waiting for you to log in...")
        print("(Press Ctrl+C when done)")

        try:
            # 等待用户登录，每5秒检查一次
            while True:
                await asyncio.sleep(5)
                cookies = await context.cookies()
                cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
                print(f"  Cookies: {len(cookies)} items", end="\r")
        except KeyboardInterrupt:
            print("\n\nSaving cookies...")
            cookies = await context.cookies()

            # 保存 Cookie 到文件
            cookie_dir = os.path.join(os.path.dirname(__file__), "cookies")
            os.makedirs(cookie_dir, exist_ok=True)

            cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
            cookie_file = os.path.join(cookie_dir, f"{platform}_cookies.txt")
            with open(cookie_file, "w", encoding="utf-8") as f:
                f.write(cookie_str)

            json_file = os.path.join(cookie_dir, f"{platform}_cookies.json")
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)

            print(f"Saved {len(cookies)} cookies to:")
            print(f"  {cookie_file}")
            print(f"  {json_file}")

        await context.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manual_login.py <platform>")
        print(f"Platforms: {', '.join(PLATFORMS.keys())}")
        sys.exit(1)

    asyncio.run(manual_login(sys.argv[1]))
