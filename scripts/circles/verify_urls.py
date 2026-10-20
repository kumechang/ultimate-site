#!/usr/bin/env python3
"""候補CSVの official_url が「生きていて、アルティメット団体のページか」を検証する。

公開前の作業用ツール。判定は目安であり、最終的な公開可否は必ず人が確認する。
法務レビューの運用ルールに従い、SNS（X/Instagram/Facebook/YouTube/LINE）は取得しない。

使い方: python3 scripts/circles/verify_urls.py --in candidates.csv --out verified.csv
入力CSVの列: university_name, official_url（複数ある場合は最初の1件）, team_names_pdf,
team_names_jfda_registry, user_list_note（団体名の照合用。無くても動く）

verdict:
  ok               タイトルにアルティメット/団体名があり、団体固有のページと見られる
  list_page        大学公式の団体一覧ページ等に団体の記載がある（団体固有のURLではない）
  needs_human      自動では判断できない（JS描画・画像のみなど）
  dead / access_denied / unreachable / robots_blocked / sns_not_checked / no_url / invalid_url
"""
import argparse
import csv
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
import urllib.robotparser
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

USER_AGENT = "UltimateNaviBot/1.0 (+contact@ultimate-navi.com)"
REQUEST_INTERVAL_SEC = 10  # 同一ホストへのアクセス間隔
TIMEOUT_SEC = 20
MAX_BYTES = 500_000
CACHE_DAYS = 30
SNS_HOSTS = ("x.com", "twitter.com", "instagram.com", "facebook.com", "fb.com", "youtube.com", "youtu.be", "line.me")
KEYWORDS = ("アルティメット", "ultimate", "フライングディスク", "フリスビー")

_last_request = {}
_robots = {}


def squash(text):
    """比較用に正規化する（全半角統一・小文字化・記号と空白を除去）。"""
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", text).lower())


def host_is_sns(host):
    return any(host == h or host.endswith("." + h) for h in SNS_HOSTS)


def open_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "ja"})
    return urllib.request.urlopen(req, timeout=TIMEOUT_SEC)


def robots_allows(url):
    """RFC 9309に従う: 200は解釈、4xxは制限なし、5xx・通信失敗は取得を控える。"""
    p = urlparse(url)
    if p.netloc not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            with open_url(f"{p.scheme}://{p.netloc}/robots.txt") as resp:
                rp.parse(resp.read(MAX_BYTES).decode("utf-8", errors="replace").splitlines())
        except urllib.error.HTTPError as e:
            rp = None if 400 <= e.code < 500 else False
        except Exception:
            rp = False
        _robots[p.netloc] = rp
    rp = _robots[p.netloc]
    if rp is None:
        return True
    return False if rp is False else rp.can_fetch(USER_AGENT, url)


def decode(body, content_type):
    charset = None
    m = re.search(r"charset=([\w-]+)", content_type or "", re.I)
    if m:
        charset = m.group(1)
    else:
        m = re.search(rb"charset=[\"']?([\w-]+)", body[:2000], re.I)
        charset = m.group(1).decode() if m else None
    for enc in [charset, "utf-8", "cp932", "euc-jp"]:
        if not enc:
            continue
        try:
            return body.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return body.decode("utf-8", errors="replace")


def fetch(url, cache, cache_path):
    """{status, final_url, title, text, error} を返す。取得済み(30日以内)ならキャッシュを使う。"""
    hit = cache.get(url)
    if hit and "links" in hit and (datetime.now() - datetime.fromisoformat(hit["fetched_at"])).days < CACHE_DAYS:
        return hit
    host = urlparse(url).netloc
    wait = REQUEST_INTERVAL_SEC - (time.time() - _last_request.get(host, 0))
    if host in _last_request and wait > 0:
        time.sleep(wait)
    out = {"status": None, "final_url": url, "title": "", "text": "", "links": [], "error": "", "fetched_at": datetime.now().isoformat()}
    try:
        with open_url(url) as resp:
            html = decode(resp.read(MAX_BYTES), resp.headers.get("Content-Type"))
            out.update(status=resp.status, final_url=resp.geturl())
        title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
        out["title"] = re.sub(r"\s+", " ", title.group(1)).strip() if title else ""
        out["links"] = sorted(set(re.findall(r"""(?:href|src)=["']([^"']+)["']""", html)))[:1000]
        out["text"] = re.sub(r"\s+", " ", re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", html, flags=re.S | re.I))[:200_000]
    except urllib.error.HTTPError as e:
        out["status"] = e.code
    except Exception as e:  # DNS失敗・証明書エラー・タイムアウトなど
        out["error"] = f"{type(e).__name__}: {e}"
    _last_request[host] = time.time()
    cache[url] = out
    cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return out


def canon_url(url):
    """リンク照合用にURLを正規化する（スキーム・www・末尾スラッシュ・クエリ・twitter→xの差を吸収）。"""
    u = re.sub(r"^https?://", "", url.strip().lower()).split("#")[0].split("?")[0]
    u = re.sub(r"^(www\.|m\.|mobile\.)", "", u).replace("twitter.com/", "x.com/")
    return u.rstrip("/")


def check_sns(row, links):
    """sns_urls の各URLが、公式ページ内のリンクに含まれるか確認する。"""
    page_links = {canon_url(l) for l in links if l.startswith(("http://", "https://", "//"))}
    page_links |= {canon_url("https:" + l) for l in links if l.startswith("//")}
    found, missing = [], []
    for part in (row.get("sns_urls") or "").split(";"):
        m = re.search(r"https?://\S+", part)
        if not m or canon_url(m.group(0)) in ("facebook.com", "instagram.com", "x.com"):
            continue  # ユーザー名を含まない汎用URLは対象外
        (found if canon_url(m.group(0)) in page_links else missing).append(part.strip())
    return found, missing


def team_tokens(row):
    raw = " ; ".join(row.get(k, "") for k in ("team_names_pdf", "team_names_jfda_registry", "user_list_note"))
    parts = (t.strip() for t in re.split(r"[/;；、]", raw))
    return {squash(t) for t in parts if len(squash(t)) >= 2 and not t.startswith("(")}


def verify(row, cache, cache_path):
    url = (row.get("official_url") or "").split(";")[0].strip()
    res = {"http_status": "", "final_url": "", "redirected_to_other_domain": "", "page_title": "",
           "mentions_ultimate": "", "mentions_team_name": "", "verdict": "", "verify_note": "",
           "sns_found_on_official_page": "", "sns_not_found_on_page": "", "verified_date": date.today().isoformat()}
    if not url:
        return {**res, "verdict": "no_url"}
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return {**res, "verdict": "invalid_url"}
    if host_is_sns(parsed.netloc):
        return {**res, "verdict": "sns_not_checked", "verify_note": "SNSは自動取得しない運用のため未検証（人が目視で確認）"}
    if not robots_allows(url):
        return {**res, "verdict": "robots_blocked", "verify_note": "robots.txtにより取得しない（人が目視で確認）"}

    page = fetch(url, cache, cache_path)
    res.update(http_status=page["status"] or "", final_url=page["final_url"], page_title=page["title"])
    if page["error"]:
        return {**res, "verdict": "unreachable", "verify_note": page["error"]}
    res["redirected_to_other_domain"] = "yes" if urlparse(page["final_url"]).netloc != parsed.netloc else "no"
    if page["status"] in (401, 403, 429):
        return {**res, "verdict": "access_denied", "verify_note": "サーバーが自動アクセスを断っている（リンク切れとは限らない。人が目視で確認）"}
    if page["status"] >= 400:
        return {**res, "verdict": "dead"}

    tokens = team_tokens(row)
    title_sq, body_sq = squash(page["title"]), squash(page["text"])
    kw = [squash(k) for k in KEYWORDS]
    in_title = any(k in title_sq for k in kw) or any(t in title_sq for t in tokens)
    mentions = any(k in body_sq for k in kw) or in_title
    team = any(t in body_sq for t in tokens) or any(t in title_sq for t in tokens)
    res.update(mentions_ultimate="yes" if mentions else "no", mentions_team_name="yes" if team else "no")
    found, missing = check_sns(row, page.get("links", []))
    res.update(sns_found_on_official_page=" ; ".join(found), sns_not_found_on_page=" ; ".join(missing))

    notes = []
    if res["redirected_to_other_domain"] == "yes":
        notes.append("別ドメインへ転送（ドメイン売却・移転の可能性）")
    if in_title and not notes:
        res["verdict"] = "ok"
    elif mentions and team:
        res["verdict"] = "list_page"
        notes.append("タイトルに団体名なし。大学の一覧ページ等に記載がある（団体固有のURLではない）")
    else:
        res["verdict"] = "needs_human"
        notes.append("本文から団体を確認できない（JS描画・画像のみの可能性）")
    res["verify_note"] = " / ".join(notes)
    return res


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--in", dest="src", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--cache", default="/tmp/ultimate-navi-circles/verify-cache.json", help="取得結果のキャッシュ（30日）")
    args = parser.parse_args()

    cache_path = Path(args.cache)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}

    with open(args.src, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows, fields = list(reader), list(reader.fieldnames)
    added = ["http_status", "final_url", "redirected_to_other_domain", "page_title", "mentions_ultimate",
             "mentions_team_name", "verdict", "verify_note", "sns_found_on_official_page", "sns_not_found_on_page", "verified_date"]
    counts = {}
    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields + [c for c in added if c not in fields], extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            res = verify(row, cache, cache_path)
            counts[res["verdict"]] = counts.get(res["verdict"], 0) + 1
            if res["verdict"] not in ("no_url", "sns_not_checked"):
                print(f'{row["university_name"]}: {res["verdict"]} ({res["http_status"]}) {res["verify_note"]}', file=sys.stderr)
            writer.writerow({**row, **res})
    print("結果:", counts, f"→ {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
