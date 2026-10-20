#!/usr/bin/env python3
"""動画CSVのYouTube動画が「生きていて、埋め込み可能か」をoEmbed（公式）で確認する。

動画の埋め込みは、公開後にも非公開化・削除・埋め込み禁止になることがあるため、定期的な確認に使う。
動画ページそのものは取得せず、oEmbedエンドポイント（robots.txtで禁止されていない公式の確認用API）のみ使う。

使い方: python3 scripts/videos/verify_youtube.py --in videos.csv --out videos-verified.csv
入力CSVの列: URL（watch?v=... 形式。他の列は保持される）
verdict: embeddable / embed_disabled(401) / not_found(404) / error
"""
import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

USER_AGENT = "UltimateNaviBot/1.0 (+contact@ultimate-navi.com)"
REQUEST_INTERVAL_SEC = 10  # 同一ホストへのアクセス間隔
TIMEOUT_SEC = 20
ID_RE = re.compile(r"(?:v=|youtu\.be/|/shorts/|/embed/)([\w-]{11})")


def video_id(url):
    m = ID_RE.search(url or "")
    return m.group(1) if m else ""


def check(vid):
    watch = f"https://www.youtube.com/watch?v={vid}"
    api = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(watch, safe="")
    req = urllib.request.Request(api, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {"verdict": "embeddable", "http_status": 200, "oembed_title": data.get("title", ""),
                "oembed_author": data.get("author_name", ""), "note": ""}
    except urllib.error.HTTPError as e:
        verdict = {401: "embed_disabled", 404: "not_found"}.get(e.code, "error")
        return {"verdict": verdict, "http_status": e.code, "oembed_title": "", "oembed_author": "", "note": ""}
    except Exception as e:
        return {"verdict": "error", "http_status": "", "oembed_title": "", "oembed_author": "",
                "note": f"{type(e).__name__}: {e}"}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--in", dest="src", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    with open(args.src, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows, fields = [r for r in reader if (r.get("URL") or "").strip()], list(reader.fieldnames)
    added = ["video_id", "verdict", "http_status", "oembed_title", "oembed_author", "title_matches_csv", "note", "checked_date"]
    counts = {}
    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields + [c for c in added if c not in fields])
        writer.writeheader()
        for i, row in enumerate(rows):
            vid = video_id(row["URL"])
            if i:
                time.sleep(REQUEST_INTERVAL_SEC)
            res = check(vid) if vid else {"verdict": "error", "http_status": "", "oembed_title": "", "oembed_author": "", "note": "動画IDを取得できない"}
            res["title_matches_csv"] = "" if res["verdict"] != "embeddable" else ("yes" if res["oembed_title"].strip() == (row.get("タイトル") or "").strip() else "no")
            counts[res["verdict"]] = counts.get(res["verdict"], 0) + 1
            print(f'[{i + 1}/{len(rows)}] {vid}: {res["verdict"]} {row.get("タイトル", "")[:30]}', file=sys.stderr)
            writer.writerow({**row, "video_id": vid, **res, "checked_date": date.today().isoformat()})
    print("結果:", counts, f"→ {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
