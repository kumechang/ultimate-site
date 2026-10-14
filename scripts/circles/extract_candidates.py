#!/usr/bin/env python3
"""JFDAの全日本大学選手権・関東予選PDFから、大学アルティメット団体の「候補」を抽出する。

公開前の作業用ツール。出力は人が公式URLを調べて確認するための候補リストであり、
そのまま公開してはいけない（docs: 掲載項目は大学名・団体名・公式リンク・最終確認日のみ）。

要件: python3 + pypdf (pip install pypdf)
使い方: python3 scripts/circles/extract_candidates.py --out candidates.csv
"""
import argparse
import csv
import re
import sys
import time
import unicodedata
import urllib.request
import urllib.robotparser
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

# 暗号化PDFは扱わないため、環境によっては壊れていることがあるcryptographyを読み込ませない
sys.modules.setdefault("cryptography", None)
from pypdf import PdfReader  # noqa: E402

USER_AGENT = "UltimateNaviBot/1.0 (+contact@ultimate-navi.com)"
REQUEST_INTERVAL_SEC = 10  # 同一ホストへのアクセス間隔（法務レビューの運用ルール）
TIMEOUT_SEC = 30

# 年度ごとにURLが変わるため、年度ページ(https://www.jfda.or.jp/alljapan-university-ultimate/)で確認して更新する
DEFAULT_PDFS = [
    (2026, "https://www.jfda.or.jp/web/wp/wp-content/uploads/2026/07/2026AJUUC_Kanto_Seeding_20260715.pdf"),
    (2025, "https://www.jfda.or.jp/web/wp/wp-content/uploads/2025/07/2025AJUUC_Kanto_Seeding_20250716.pdf"),
]
# 文部科学省 学校コード一覧（大学・短大・高専）。出典: https://www.mext.go.jp/b_menu/toukei/mext_01087.html
# 利用規約: 政府標準利用規約（出典明記）。毎年更新されるため最新のCSVに差し替える
MEXT_CSV_URL = "https://www.mext.go.jp/content/20260825-mxt_chousa01-000011635_6.csv"

# 旧字体 → 新字体（表記ゆれ吸収用。同じ文字数で置換する）
OLD_TO_NEW = str.maketrans({"學": "学", "國": "国", "應": "応", "獨": "独", "澤": "沢"})

PAGE_MIDDLE_X = 300  # この座標より左の文字をオープン部門（左列）、右をウィメン部門（右列）とみなす
ENTRY_RE = re.compile(r"(\d+)\s+(.+?)\s+([A-D])(?=\s+\d+\s|\s*$)")

_last_request_at = {}
_robots = {}


def polite_fetch(url, cache_dir):
    """robots.txtを守り、同一ホストに間隔を空けて1回だけ取得する。取得済みならキャッシュを使う。"""
    cache_dir.mkdir(parents=True, exist_ok=True)
    dest = cache_dir / Path(urlparse(url).path).name
    if dest.exists():
        return dest

    parsed = urlparse(url)
    host = parsed.netloc
    if host not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"{parsed.scheme}://{host}/robots.txt")
        rp.read()
        _robots[host] = rp
    if not _robots[host].can_fetch(USER_AGENT, url):
        sys.exit(f"robots.txtで禁止されているため取得しません: {url}")

    wait = REQUEST_INTERVAL_SEC - (time.time() - _last_request_at.get(host, 0))
    if wait > 0 and host in _last_request_at:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
        dest.write_bytes(resp.read())
    _last_request_at[host] = time.time()
    return dest


def normalize(text):
    return unicodedata.normalize("NFKC", text).translate(OLD_TO_NEW)


def load_universities(mext_csv):
    """MEXTのCSVから、現存する大学（本校）の {正規化名: (表示名, 都道府県)} を返す。"""
    unis = {}
    with open(mext_csv, encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if len(row) < 10 or not row[1].startswith("F1") or not row[4].startswith("1"):
                continue
            if row[9]:  # 属性情報廃止年月日
                continue
            prefecture = re.sub(r"^\d+\(|\)$", "", row[2])
            unis[normalize(row[5]).replace(" ", "")] = (row[5], prefecture)
    return unis


def parse_pdf(path, year):
    """PDFから (year, division, rank, raw_name) のリストを返す。左列=オープン、右列=ウィメン。"""
    teams = []
    last = {"open": 0, "women": 0}
    for page in PdfReader(str(path)).pages:
        fragments = []  # (x座標, テキスト)。順位が重なる行の左右判定に使う
        page.extract_text(visitor_text=lambda text, cm, tm, font, size: fragments.append((tm[4], text)))
        for line in (page.extract_text() or "").splitlines():
            found = ENTRY_RE.findall(line)
            if len(found) == 2:
                divisions = ["open", "women"]
            elif len(found) == 1:
                rank = int(found[0][0])
                fits_open = last["open"] + 1 == rank
                fits_women = last["women"] + 1 == rank
                if fits_open and not fits_women:
                    divisions = ["open"]
                elif fits_women and not fits_open:
                    divisions = ["women"]
                else:
                    name = re.sub(r"\s", "", found[0][1])
                    xs = [x for x, t in fragments if name in re.sub(r"\s", "", t)]
                    divisions = [("open" if min(xs) < PAGE_MIDDLE_X else "women") if xs else "unknown"]
            else:
                continue
            for division, (rank, name, _schedule) in zip(divisions, found):
                if division in last:
                    last[division] = int(rank)
                teams.append((year, division, int(rank), name))
    return teams


def split_university(raw_name, unis_by_len):
    """'慶應義塾大学ホワイトホーンズ' → (MEXT上の大学名, 都道府県, チーム名)。見つからなければ None。"""
    compact = unicodedata.normalize("NFKC", re.sub(r"\s", "", raw_name))
    matching_key = compact.translate(OLD_TO_NEW)
    for key, (display, prefecture) in unis_by_len:
        if matching_key.startswith(key):
            return display, prefecture, compact[len(key):]
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="circle-candidates.csv", help="出力CSV（UTF-8 BOM付き。Excel/スプレッドシートで開ける）")
    parser.add_argument("--cache-dir", default="/tmp/ultimate-navi-circles", help="取得したPDF/CSVの保存先")
    parser.add_argument("--pdf", action="append", metavar="YEAR=URL", help="対象PDF（複数指定可）。省略時は既定のURL")
    args = parser.parse_args()

    pdfs = DEFAULT_PDFS
    if args.pdf:
        pdfs = [(int(y), u) for y, u in (a.split("=", 1) for a in args.pdf)]

    cache_dir = Path(args.cache_dir)
    unis = load_universities(polite_fetch(MEXT_CSV_URL, cache_dir))
    unis_by_len = sorted(unis.items(), key=lambda kv: len(kv[0]), reverse=True)
    print(f"MEXT: 現存する大学 {len(unis)} 校を読み込み", file=sys.stderr)

    rows = defaultdict(lambda: {"teams": [], "divisions": set(), "years": set(), "sources": set()})
    unmatched = []
    for year, url in pdfs:
        path = polite_fetch(url, cache_dir)
        teams = parse_pdf(path, year)
        counts = defaultdict(int)
        for _y, division, _rank, _name in teams:
            counts[division] += 1
        print(f"{year}: {path.name} → {dict(counts)}", file=sys.stderr)
        for _y, division, _rank, raw in teams:
            split = split_university(raw, unis_by_len)
            if split is None:
                unmatched.append((year, division, raw))
                continue
            university, prefecture, team = split
            entry = rows[(university, prefecture)]
            if team and team not in entry["teams"]:
                entry["teams"].append(team)
            entry["divisions"].add(division)
            entry["years"].add(year)
            entry["sources"].add(path.name)

    today = date.today().isoformat()
    header = ["university_name", "prefecture", "in_tokyo", "team_names", "divisions", "seen_years",
              "source_pdfs", "official_url", "sns_urls", "notes", "status", "retrieved_date"]
    ordered = sorted(rows.items(), key=lambda kv: (kv[0][1] != "東京", kv[0][0]))
    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for (university, prefecture), e in ordered:
            writer.writerow([
                university, prefecture, "yes" if prefecture == "東京" else "no",
                " / ".join(e["teams"]), "/".join(sorted(e["divisions"])),
                "/".join(str(y) for y in sorted(e["years"])), " ; ".join(sorted(e["sources"])),
                "", "", "", "candidate", today,
            ])

    tokyo = sum(1 for (_u, p), _e in ordered if p == "東京")
    print(f"候補: {len(ordered)} 校（うち東京 {tokyo} 校）→ {args.out}", file=sys.stderr)
    if unmatched:
        print("大学名に照合できなかった行（要確認。クラブチームなど）:", file=sys.stderr)
        for year, division, raw in unmatched:
            print(f"  {year} {division}: {raw}", file=sys.stderr)


if __name__ == "__main__":
    main()
