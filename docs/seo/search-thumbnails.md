# 検索結果・SNS共有の画像（サムネイル）対応

- 実施日: 2026-10-27
- 背景: Bingの検索結果で、競合サイトにはサムネイル画像が出ているのに、当サイトには出ていなかった。

## 何をしたか
- 記事ごとの `og:image` / `twitter:image` を、そのページのヒーロー画像から作ったJPEG（16:9、1200×675）にした。
  - これまでは全ページ共通の `og-default.png`（ロゴ入りの汎用画像）だった。
  - 画像がない記事・一覧・用語集は、従来どおり `og-default.png`。
- `og:image:width` / `height` / `alt` を追加。
- 記事の構造化データ（Article）に `image`（16:9・4:3・1:1の3枚）を追加。
- `<meta name="robots" content="max-image-preview:large">` を追加（noindexのページは従来どおり）。
- ホームの `og:image` を、写真ベースの画像に変更。

## 画像の作り方
- `public/images/photos/` の写真から、`node scripts/images/make_og_images.mjs` で `public/images/og/` に生成する（生成物はコミットする）。
- 写真を追加・差し替えたら、スクリプトを再実行する。
- 元画像より大きくは拡大しない（小さい写真は小さいまま出力）。
- 記事に合わない写真は、スクリプトの `SKIP` に入れると、その記事は共通画像になる（現在は `/start/cost/` のサッカー写真）。

## 注意点・限界
- どの画像をサムネイルにするかは、BingやGoogleが自動で決める。指定はできないため、出る保証はない。
- 反映までは数日〜数週間かかる。確認は、Bing Webmaster Tools / Search Console のURL検査で、`og:image` が取得できているかを見る。
- 更新したURLは、`python3 scripts/seo/indexnow.py --url <URL>` でBingに通知できる。
- 写真が少ないため、同じ写真を複数の記事で使っている。罰則はないが、検索結果で見分けにくくなる。記事ごとに固有の写真を足せると効果が高い。
- `/start/cost/` のヒーロー画像は、サッカーの写真で、記事の内容と合っていない。差し替えが望ましい。
