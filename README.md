# ultimate-site

アルティメット（フライングディスク競技）初心者向けの情報サイト。Amazonアソシエイトを活用したアフィリエイト導線を組み込みつつ、SEOに強い情報サイトを目指しています。

## 技術スタック

- [Astro](https://astro.build/)（静的サイト生成）
- Markdown / MDX（記事コンテンツ）
- Tailwind CSS v4
- `@astrojs/sitemap`（sitemap自動生成）

## ディレクトリ構成

```
src/
  content/
    basics/    アルティメットとは・基本ルール・ポジション・戦術
    gear/      必須アイテム（★アフィリエイト記事）
    skills/    基本技術（スロー解説など）
    start/     始め方・コミュニティ
    glossary/  用語集（用語ごとに1ファイル）
  content.config.ts   コンテンツコレクションのスキーマ定義
  components/  Header, Footer, Seo, AffiliateCard など共通コンポーネント
  layouts/     BaseLayout, ArticleLayout
  pages/       ルーティング（各コレクションの index / [slug] ページ）
```

## 記事の追加方法

該当するディレクトリ（例: `src/content/gear/`）に `.md`（アフィリエイトリンクなど埋め込みが不要な記事）または `.mdx`（`<AffiliateCard />` などコンポーネントを使う記事）ファイルを追加するだけで、自動的にページが生成されます。

Frontmatter例:

```md
---
title: 記事タイトル
description: メタディスクリプション用の説明文
pubDate: 2026-09-16
order: 1
---
```

## Amazonアフィリエイトリンクの設定

`gear` 配下の記事内にある `<AffiliateCard amazonUrl="#TODO-..." />` のURLを、取得したAmazonアソシエイトリンクに差し替えてください。フッターの開示文（`src/consts.ts` の `AFFILIATE_DISCLOSURE`）は規約に沿って必ず表示する運用にしています。

## 開発

```bash
npm install
npm run dev      # 開発サーバー
npm run build    # 本番ビルド（dist/ に出力）
npm run preview  # ビルド結果のプレビュー
```

## 公開状況

- 本番URL: https://ultimate-navi.com/（Cloudflare Pages、GitHub連携で自動デプロイ）

## 残タスク

- [ ] `public/og-default.png`（OGP画像）を追加
- [ ] Amazonアソシエイトの商品リンクを実際のURLに差し替え
- [ ] Google Search Console / Analytics の設置
