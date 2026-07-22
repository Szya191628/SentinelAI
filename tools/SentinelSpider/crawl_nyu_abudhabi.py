#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NYU Abu Dhabi 社交媒体爬取脚本
使用 MediaCrawler 直接爬取指定关键词的内容
"""

import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# 项目路径
SENTINEL_SPIDER_PATH = Path(__file__).resolve().parent
MEDIACRAWLER_PATH = SENTINEL_SPIDER_PATH / "DeepSentimentCrawling" / "MediaCrawler"

# NYU Abu Dhabi 相关关键词
NYU_AD_KEYWORDS = [
    "NYU Abu Dhabi",
    "纽约大学阿布扎比",
    "NYUAD",
    "纽约大学阿布扎比分校",
    "New York University Abu Dhabi",
]

def check_mediacrawler():
    """检查 MediaCrawler 是否存在"""
    if not MEDIACRAWLER_PATH.exists():
        print(f"[ERROR] MediaCrawler directory not found: {MEDIACRAWLER_PATH}")
        return False

    main_py = MEDIACRAWLER_PATH / "main.py"
    if not main_py.exists():
        print(f"[ERROR] MediaCrawler main.py not found: {main_py}")
        return False

    print(f"[OK] MediaCrawler path: {MEDIACRAWLER_PATH}")
    return True

def configure_mediacrawler(platform: str, keywords: list, max_notes: int = 50):
    """配置 MediaCrawler 的 base_config.py"""
    base_config_path = MEDIACRAWLER_PATH / "config" / "base_config.py"

    if not base_config_path.exists():
        print(f"[ERROR] base_config.py not found: {base_config_path}")
        return False

    # 读取原始配置
    with open(base_config_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 关键词字符串
    keywords_str = ",".join(keywords)

    # 修改关键配置项
    lines = content.split('\n')
    new_lines = []

    for line in lines:
        if line.startswith('PLATFORM = '):
            new_lines.append(f'PLATFORM = "{platform}"  # xhs | dy | ks | bili | wb | tieba | zhihu')
        elif line.startswith('KEYWORDS = '):
            new_lines.append(f'KEYWORDS = "{keywords_str}"  # 关键词搜索配置')
        elif line.startswith('CRAWLER_TYPE = '):
            new_lines.append('CRAWLER_TYPE = "search"  # search(关键词搜索)')
        elif line.startswith('SAVE_DATA_OPTION = '):
            new_lines.append('SAVE_DATA_OPTION = "csv"  # 保存为CSV，无需数据库')
        elif line.startswith('CRAWLER_MAX_NOTES_COUNT = '):
            new_lines.append(f'CRAWLER_MAX_NOTES_COUNT = {max_notes}')
        elif line.startswith('ENABLE_GET_COMMENTS = '):
            new_lines.append('ENABLE_GET_COMMENTS = True')
        elif line.startswith('CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES = '):
            new_lines.append('CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES = 20')
        elif line.startswith('HEADLESS = '):
            new_lines.append('HEADLESS = False  # 显示浏览器便于扫码登录')
        else:
            new_lines.append(line)

    # 写入新配置
    with open(base_config_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print(f"[OK] Configured MediaCrawler:")
    print(f"   Platform: {platform}")
    print(f"   Keywords: {keywords}")
    print(f"   Max notes: {max_notes}")
    return True

def run_crawler(platform: str, login_type: str = "qrcode"):
    """运行爬虫"""
    print(f"\n[START] Crawling {platform}...")
    print(f"   Login type: {login_type}")
    print(f"   Note: First time requires QR code scan")

    cmd = [
        sys.executable, "main.py",
        "--platform", platform,
        "--lt", login_type,
        "--type", "search",
        "--save_data_option", "csv"
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=MEDIACRAWLER_PATH,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        if result.returncode == 0:
            print(f"[OK] {platform} crawl completed!")
            return True
        else:
            print(f"[FAIL] {platform} crawl failed, return code: {result.returncode}")
            return False

    except KeyboardInterrupt:
        print("\n[WARN] User interrupted")
        return False
    except Exception as e:
        print(f"[ERROR] Crawl exception: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="NYU Abu Dhabi Social Media Crawler"
    )

    parser.add_argument(
        "--platform",
        type=str,
        nargs='+',
        choices=['xhs', 'dy', 'ks', 'bili', 'wb', 'tieba', 'zhihu'],
        default=['xhs', 'wb', 'zhihu'],
        help="Platform to crawl (default: xhs wb zhihu)"
    )

    parser.add_argument(
        "--max-notes",
        type=int,
        default=50,
        help="Max notes per keyword (default: 50)"
    )

    parser.add_argument(
        "--login-type",
        type=str,
        choices=['qrcode', 'phone', 'cookie'],
        default='qrcode',
        help="Login type (default: qrcode)"
    )

    parser.add_argument(
        "--keywords",
        type=str,
        default=None,
        help="Custom keywords, comma separated"
    )

    parser.add_argument(
        "--list-keywords",
        action="store_true",
        help="Show default keywords"
    )

    args = parser.parse_args()

    # 显示关键词
    if args.list_keywords:
        print("Default keywords:")
        for i, kw in enumerate(NYU_AD_KEYWORDS, 1):
            print(f"  {i}. {kw}")
        return

    # 检查 MediaCrawler
    if not check_mediacrawler():
        sys.exit(1)

    # 解析关键词
    if args.keywords:
        keywords = [kw.strip() for kw in args.keywords.split(',')]
    else:
        keywords = NYU_AD_KEYWORDS

    print("=" * 60)
    print("NYU Abu Dhabi Social Media Crawler")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Keywords: {keywords}")
    print(f"Platforms: {args.platform}")
    print(f"Max notes per keyword: {args.max_notes}")
    print(f"Login type: {args.login_type}")
    print("=" * 60)

    # 逐平台爬取
    results = {}
    for platform in args.platform:
        print(f"\n{'='*40}")
        print(f"Processing platform: {platform}")
        print(f"{'='*40}")

        # 配置
        if not configure_mediacrawler(platform, keywords, args.max_notes):
            results[platform] = False
            continue

        # 运行爬虫
        success = run_crawler(platform, args.login_type)
        results[platform] = success

    # 显示结果摘要
    print("\n" + "=" * 60)
    print("Crawl Results Summary")
    print("=" * 60)

    for platform, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        print(f"  {platform}: {status}")

    successful = sum(1 for s in results.values() if s)
    total = len(results)
    print(f"\n  Success: {successful}/{total}")

    # 提示数据位置
    print(f"\nData saved to:")
    print(f"  {MEDIACRAWLER_PATH / 'data'}")
    print("Check CSV files for results")

if __name__ == "__main__":
    main()
