#!/usr/bin/env python3
"""IndexNow（Bing等への更新通知）で、サイトのURLを送信する。

事前に、公開済みの public/eb415e53c557e6300b6a0c12ce21331f.txt が https://ultimate-navi.com/eb415e53c557e6300b6a0c12ce21331f.txt で見えている必要がある。
サイトマップ(sitemap-0.xml)のURLを送るのが基本。一部だけ送る場合は --url を繰り返し指定する。

使い方:
  python3 scripts/seo/indexnow.py --dry-run          # 送信先とURL数だけ確認
  python3 scripts/seo/indexnow.py                    # サイトマップの全URLを送信
  python3 scripts/seo/indexnow.py --url https://ultimate-navi.com/basics/super-plays/
"""
import argparse
import json
import re
import urllib.request

HOST = "ultimate-navi.com"
KEY = "eb415e53c557e6300b6a0c12ce21331f"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
SITEMAP = f"https://{HOST}/sitemap-0.xml"
ENDPOINT = "https://api.indexnow.org/indexnow"
USER_AGENT = "UltimateNaviBot/1.0 (+contact@ultimate-navi.com)"


def fetch(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, resp.read().decode("utf-8", "replace")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", action="append", help="送信するURL（省略時はサイトマップの全URL）")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    urls = args.url
    if not urls:
        _, xml = fetch(SITEMAP)
        urls = re.findall(r"<loc>([^<]+)</loc>", xml)
    urls = [u for u in urls if u.startswith(f"https://{HOST}/")]
    print(f"{len(urls)} URLs -> {ENDPOINT} (keyLocation: {KEY_LOCATION})")
    if args.dry_run:
        return

    # 鍵ファイルが公開されていないと、送信は無効になる
    status, body = fetch(KEY_LOCATION)
    if status != 200 or body.strip() != KEY:
        raise SystemExit(f"鍵ファイルを確認できません: {KEY_LOCATION}")

    payload = json.dumps({"host": HOST, "key": KEY, "keyLocation": KEY_LOCATION, "urlList": urls}).encode("utf-8")
    status, body = fetch(ENDPOINT, payload, {"Content-Type": "application/json; charset=utf-8"})
    print("結果:", status, body[:200])


if __name__ == "__main__":
    main()
