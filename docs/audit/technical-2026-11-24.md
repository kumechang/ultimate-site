# 技術SEO・構造監査（2026-11-24）

対象: https://ultimate-navi.com（`npm run build` の出力 39 ページ、HTML 全数）。`src/` `public/` は未編集。
下の差分は、作業コピーに当てて `npm run build` が通ることまで確認済み（本リポジトリには未適用）。

## 0. 要約

| # | 優先度 | 問題 | 影響 |
|---|---|---|---|
| 1 | **高** | `window.gtag` が未定義で、`internal_nav` と `amazon_link_click` が一度も送信されていない | 11/10 の導線施策（gear-funnel）の効果測定が成立しない |
| 2 | **高** | `/glossary/` が全 12 用語の本文を表示し、個別ページとほぼ同一 | 正規URLの競合・重複扱い、見出し構造の崩れ |
| 3 | 中 | 記事ヒーロー画像が 2000px の AVIF（117〜600KB）のまま全端末に配信される。gloves は PNG 465KB | LCP・モバイル通信量 |
| 4 | 中 | Amazon 商品画像を 80px 表示に 1000〜1500px 版で配信（accessories で約 1.9MB） | 通信量（lazy だがスクロールで取得） |
| 5 | 中 | 本文を修正した 16 ページで `updatedDate` が古いまま。sitemap の lastmod と画面の「更新日」「dateModified」が実態より古い。用語集・一覧ページは lastmod なし | クロール優先度・鮮度シグナルの信頼性 |
| 6 | 中 | `/_astro/*`（ハッシュ付き）も `max-age=0, must-revalidate` | 再訪時に毎回再検証 |
| 7 | 中 | 薄い用語ページ（sotg 170字、cup 258字、force 260字、break 280字） | 重複解消後も単独でインデックスされにくい |
| 8 | 中 | 計測イベントの範囲が狭い（ヘッダー／フッター／一覧／動画／用語集が未計測） | 導線の比較ができない |
| 9 | 低 | title/description の長さ、OGP 既定画像のサイズ・alt 欠落、JSON-LD の不足、内部リンクの偏り ほか | §1〜2 参照 |

問題なしと確認できた点: リンク切れ（内部 0 件、アンカー含む。外部リンクは Amazon・YouTube を除く 21 URL がすべて 200。1 件の 429 は Wikimedia のレート制限）／孤立ページ 0／全ページがトップから 2 クリック以内／title・description の重複 0／canonical は全ページ自己参照・絶対URL・末尾スラッシュ統一で sitemap と一致／noindex 0／h1 は全ページ 1 つ／画像 alt の欠落 0／JSON-LD は全ページで JSON として妥当／Amazon リンク 43 件すべて `rel="sponsored noopener"`。

---

## 1. dist 全 HTML の検査

### 1-1. title / description
- 重複なし。title は 21〜46 字＋サフィックス「 | アルティメットナビ」（12字）。記事ページは 41〜46 字になり、検索結果では末尾が省略される可能性が高い（**低**。Google が書き換えることもあり、10月の変更の測定中のため据え置きでよい）。
- description が 70 字未満のページ（**低**）: `/basics/` 52、`/glossary/turnover/` 53、`/start/find-team/` 56、`/gear/` 57、`/start/cost/` 59、`/skills/throws/` 61、`/glossary/force/` 62、`/glossary/sotg/` 62、`/gear/disc/` 64、`/start/faq/` 64、`/privacy/` 68。11/04 の方針（90〜115字）に揃えるなら、この 10 ページ（privacy を除く）が残り。

### 1-2. OGP・構造化データ（**低**）
- 既定画像 `og-default.png`（1280×720）を使う 21 ページ（about、各一覧、accessories、what-to-buy、用語集 13 ページ、privacy）は、`og:image:width/height/alt` が出ない。`Seo.astro` の既定値に追加する。

```diff
--- a/src/components/Seo.astro
+++ b/src/components/Seo.astro
@@
-  image = '/og-default.png',
-  imageWidth,
-  imageHeight,
-  imageAlt,
+  image = '/og-default.png',
+  imageWidth = image === '/og-default.png' ? 1280 : undefined,
+  imageHeight = image === '/og-default.png' ? 720 : undefined,
+  imageAlt = image === '/og-default.png' ? SITE_TITLE : undefined,
```
- `Organization` は name と url のみ。トップだけ `WebSite`（name と alternateName）を足し、`Organization` に `logo`（`/apple-touch-icon.png`、180px）を付けると、サイト名表示の手がかりになる。
- `Article` の `image` がないページが 14（accessories、what-to-buy、用語集 12）。`datePublished` が用語集は `[slug].astro` の固定値 `2026-09-16`。`publisher` / `mainEntityOfPage` なし。
- `FAQPage`（`/start/faq/`）は、一般サイトでは Google のリッチリザルトの対象外（2023年以降）。質問文が `start/[slug].astro` に二重管理されている。残すなら frontmatter に寄せて同期ずれを防ぐ（**低**）。

### 1-3. 見出し・画像
- h1 は全 39 ページで 1 つ、階層の飛びなし。トップだけ h1 が `<main>` の外（`full-bleed` スロット）にある（**低**）。
- `/glossary/` は h1 の下に、用語本文由来の h2 が 15 個並ぶ（「よくある勘違い」が 2 回、用語名の見出しはなし）。§3 で解消する。
- alt は全画像にあり。YouTube サムネイルは「動画のサムネイル：…」で適切。

---

## 2. 内部リンク

- 内部リンク 39 ページ分を走査。リンク切れ 0、孤立 0、最大深さ 2（ヘッダー／フッターを除いた本文リンクだけでも、`/about/` を除き深さ 3 以内）。
- 本文リンク元ページ数（ヘッダー／フッター／パンくずを除く）。少ない順:

| ページ | 本文被リンク | 備考 |
|---|---|---|
| `/glossary/pick/`, `/glossary/stack/`, `/glossary/throw-off/` | 2（用語集一覧＋1） | stack は 11/24 に未登録で改訂した対象 |
| `/gear/gloves/`, `/glossary/cup/`, `/glossary/traveling/` | 3 | |
| `/basics/vs-*`, `/gear/accessories/`, `/gear/apparel/`, `/glossary/break/`, `/glossary/sotg/`, `/start/annual-schedule/` | 4 | |
| 最多: `/start/what-to-buy/` 29、`/start/where-to-play/` 27、`/start/cost/` 16、`/basics/rules/` 15 | | 「次の一歩」の効果 |

- アンカーテキストは良好。「こちら」等の汎用語は 0。同一リンク先に説明的な語（「ディスクの選び方」「体験できる場所の探し方」など）が使い分けられている。
- 改善候補（**低**）
  - 本文に出ているのにリンクが未設定の語: 「プル」（tactics、what-is-ultimate、turnover → `/glossary/throw-off/`）、「グローブ」（`start/cost.md` の表 → `/gear/gloves/`）。stack は `/basics/positions/` などの「スタック」言及にリンクを足す（現状は tactics のみ）。
  - 一覧ページのカードは、`<a>` の中に h2 と説明文があり、アンカーが 100〜250 字になる。`<a>` を見出しだけに限定し、カード全体のクリックは `after:absolute after:inset-0` で実現できる。
  - ナビの「技術・用語」は `/skills/`（スロー解説のみ）を指し、用語は別の「用語集」。「基本技術」に改める。`/gear/` は h1「必須アイテムと選び方」と title が不一致。

---

## 3. 用語集（`/glossary/`）の重複

### 3-1. 現状の数値
- `/glossary/` は `render(term)` で 12 用語の本文を全部出力。本文 6,791 字、HTML 38.9KB。
- 個別ページの記事部分（合計 7,358 字）のうち、15 字以上の文 124 件中 **100 件（81%）が `/glossary/` に逐語で存在**する。ほぼ全文の複製。
- 個別ページの title は「◯◯とは？…」、`/glossary/` は「アルティメット用語集」だが、本文は同一。

### 3-2. 影響
1. **正規URLの競合**: 同じ文章が 2 つのURLにあり、Google が一覧側を代表に選ぶ、または個別ページを重複とみなす可能性がある（ペナルティではなく、インデックスからの除外）。stack を含む 4 ページが「クロール済み - インデックス未登録」だった事実と矛盾しない。ただし**因果の証拠はまだない**。確認手順: Search Console の URL 検査で、12 用語すべての「Google が選択したカノニカル」を見る。`/glossary/` と出ていれば確定。
2. **クエリの食い合い**: 「ストールカウント とは」のような単語クエリで、12 用語が混ざった長いページが出ると、検索意図との一致が弱く、クリック後の離脱につながりやすい。個別ページの title・h1・`DefinedTerm` の設計が活きない。
3. **見出し構造**: §1-3 のとおり、h2 に用語の文脈がない。
4. **薄いページの隠れ蓑**: sotg（170字）など、単独では薄いページが「一覧に載っている」ことで見えにくくなっている。

### 3-3. 案の比較
| 案 | 内容 | 評価 |
|---|---|---|
| **A（推奨）** | 一覧は「用語名＋読み＋定義の 1〜2 文（frontmatter の `description`）＋個別ページへのリンク」だけにする | 重複を解消し、個別ページが唯一の本文になる。アンカー `#stack` は `id` を残すので維持される |
| B | 全文表示を維持し、個別ページの canonical を `/glossary/#xxx` に向ける | 個別ページが検索から消える。不採用 |
| C | 個別ページを廃止して一覧に統合（301） | ロングテール（「◯◯とは」）を捨てる。不採用 |
| D | 個別ページを noindex | 同上。不採用 |

### 3-4. コード差分案（A）。ビルド確認済み
作業コピーでの結果: `/glossary/` の本文 6,791 → 1,343 字、HTML 38.9 → 20.1KB。h2 は用語ごとに 12 個。`DefinedTermSet` の JSON-LD はそのまま（`description` が可視テキストと一致）。

```diff
--- a/src/pages/glossary/index.astro
+++ b/src/pages/glossary/index.astro
@@
-import { getCollection, render } from 'astro:content';
+import { getCollection } from 'astro:content';
@@
 const terms = (await getCollection('glossary')).sort((a, b) => a.data.order - b.data.order);
-const rendered = await Promise.all(
-  terms.map(async (term) => ({ term, Content: (await render(term)).Content }))
-);
@@
-  <nav aria-label="用語一覧" class="mt-6 flex flex-wrap gap-2">
-    {terms.map((term) => (
-      <a href={`#${term.id}`} class="rounded-full border ...">{term.data.term}</a>
-    ))}
-  </nav>
-
-  <dl class="prose-article mt-8">
-    {rendered.map(({ term, Content }) => (
-      <div id={term.id} class="mb-6 scroll-mt-24 border-b border-slate-100 pb-6">
-        <dt class="text-lg font-semibold text-slate-900">
+  <ul class="mt-8 divide-y divide-slate-100">
+    {terms.map((term) => (
+      <li id={term.id} class="scroll-mt-24 py-5">
+        <h2 class="text-lg font-semibold text-slate-900">
           <a href={`/glossary/${term.id}/`} class="hover:text-sky-600">{term.data.term}</a>
           {term.data.reading && <span class="ml-2 text-xs font-normal text-slate-600">（{term.data.reading}）</span>}
-        </dt>
-        <dd class="mt-1">
-          <Content />
-        </dd>
-      </div>
+        </h2>
+        <p class="mt-1 text-sm leading-relaxed text-slate-700">{term.data.description}</p>
+        <p class="mt-1 text-sm">
+          <a href={`/glossary/${term.id}/`} class="text-sky-700 underline">{term.data.titleTerm ?? term.data.term}の意味と使い方を読む</a>
+        </p>
+      </li>
     ))}
-  </dl>
+  </ul>
 </BaseLayout>
```

適用後の運用メモ
- 個別ページの本文リンク（stack ← force など）は残るので、被リンク数は大きく減らない。一覧からの被リンクは 1 本ずつになる。
- 適用前に GSC で `/glossary/` と各用語の表示回数・順位を控えておき、約 4 週間後に比較する（11/24 の 4 ページ施策と同じやり方）。
- 一覧が約 1,300 字と短くなるので、リード文に「用語は◯語。試合の流れ別（攻撃／守備／反則）」のような分類を足すと、ハブとして機能しやすい（任意）。
- 薄い用語（sotg 170字、cup 258字、force 260字、break 280字、throw-off 368字）は、一覧からの複製がなくなると単独の弱さが露出する。600字前後（定義、例、よくある勘違い、関連用語）まで加筆するか、sotg は `/basics/what-is-ultimate/` の節へ誘導する構成を検討する（事実は公式資料のみ。既存方針どおり）。

### 3-5. sitemap の lastmod
現状（`astro.config.mjs`）:
- `DATED_COLLECTIONS` に glossary がなく、**用語集 13 ページとトップ・一覧 5 ページに lastmod がない**。コメントは「glossary には日付フィールドがない」が、現在は `updatedDate` があり 12 用語中 11 に入っている（sotg のみ未設定。最終コミットは 10/09）。
- 日付は `updatedDate ?? pubDate` を使う設計で適切。ただし運用が追いついておらず、**16 ページで本文を直したのに日付が古いまま**（下表）。Google は lastmod が実態とずれると、その値を信用しなくなる。画面の「更新日」と `Article.dateModified` も同じ値なので同時にずれている。

作業コピーで確認した差分（用語集の lastmod が出力され、一覧は配下の最新日になる）:

```diff
--- a/astro.config.mjs
+++ b/astro.config.mjs
@@
-// glossaryには日付フィールドがないため対象外（lastmodは未確定の日付を入れるより省略する）。
-const DATED_COLLECTIONS = ['basics', 'gear', 'skills', 'start'];
+// glossary は updatedDate のみ持つ（無い用語は lastmod を省略する）。
+const DATED_COLLECTIONS = ['basics', 'gear', 'skills', 'start', 'glossary'];
@@ function buildLastmodMap() {
+  // 一覧ページ（/basics/ など）は、配下の最新の更新日を使う
+  for (const collection of DATED_COLLECTIONS) {
+    const prefix = `/${collection}/`;
+    const dates = [...lastmodByPath].filter(([p]) => p.startsWith(prefix)).map(([, d]) => d.getTime());
+    if (dates.length > 0) lastmodByPath.set(prefix, new Date(Math.max(...dates)));
+  }
+
   return lastmodByPath;
 }
```
トップ `/` は、内容が変わらないので lastmod なしのままでよい。

frontmatter の日付補正案（`git log` の最終コミットに基づく。`scripts/seo/check-dates.mjs` 相当の確認結果）:

| 追加する `updatedDate` | 対象 | 根拠 |
|---|---|---|
| 2026-11-17 | basics: positions, rules, tactics, what-is-ultimate, super-plays／skills: throws／start: annual-schedule, cost, faq, find-team, where-to-play | #53 の事実訂正（公式ルール・JFDA照合） |
| 2026-10-30 | gear: accessories, apparel, disc, gloves | #50 の商品追加（11/10 は `NextStep` 追記のみで実質変更ではないため 10/30 を推奨） |
| 2026-10-09 | glossary: sotg | #41 の title/description 改善 |

再発防止（任意）: 手元で `node scripts/seo/check-dates.mjs` を実行し、表示日と最終コミット日が 7 日以上離れたファイルを列挙する。今回の実行結果は上の 16 ファイル（what-to-buy は差 7 日で対象外）。

```js
// scripts/seo/check-dates.mjs（警告のみ。CIには入れない。ビルド環境では git 履歴が浅い可能性があるため）
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = 'src/content';
const DAY = 86400000;
for (const dir of fs.readdirSync(ROOT)) {
  for (const file of fs.readdirSync(path.join(ROOT, dir))) {
    const p = path.join(ROOT, dir, file);
    const fm = fs.readFileSync(p, 'utf-8').match(/^---\n([\s\S]*?)\n---/)?.[1] ?? '';
    const shown = fm.match(/^updatedDate:\s*(\S+)/m)?.[1] ?? fm.match(/^pubDate:\s*(\S+)/m)?.[1];
    const last = execSync(`git log -1 --format=%cs -- ${p}`, { encoding: 'utf-8' }).trim();
    if (!last) continue;
    const gap = (new Date(last) - new Date(shown ?? last)) / DAY;
    if (!shown || gap > 7) console.log(`${p}: 表示日=${shown ?? '(なし)'} / 最終コミット=${last}（差${Math.round(gap)}日）`);
  }
}
```
用語集の `[slug].astro` が `pubDate` を `new Date('2026-09-16')` で固定している点も、glossary スキーマに `pubDate` を足して置き換えるのが望ましい（**低**）。

---

## 4. 表示速度・Core Web Vitals

実測ツール（Lighthouse / CrUX）は未実施。HTML・アセットの構成と実ファイルから判断した。

**良い点**: フォントは OS 標準（Web フォント 0 → CLS・FOIT なし）／CSS は 1 本 42KB（圧縮前、Tailwind v4）／ホームのヒーローは `astro:assets`（640/1280/1920 の WebP、srcset、`sizes`）／図の SVG・Amazon 画像・YouTube サムネイルは `width/height` あり／YouTube 本体はクリックまで読み込まない／GA は `async`。

### 4-1. 記事ヒーロー画像（**中**）
- `public/images/photos/*.avif` は 1600〜2000px 幅で、`srcset` なしの素の `<img>`。モバイル（約 390px）にも同じファイルを配信する。記事の LCP 要素は多くの場合この画像。`ultimate-action-01`（positions と what-is-ultimate）417KB、`rugby-lineout-night` 473KB、`disc-golf-basket-forest` 600KB。
- `gloves-illustration.png` は 1920×1080 の PNG で 465KB。
- `fetchpriority="high"` なし（ホームのヒーローも同様）。`width/height` 属性はなし（`aspect-video` で CLS は起きない）。
- 未使用: `public/images/hero-illustration.png`（544KB。参照 0 件）。

作業コピーで確認した差分（写真を `src/assets/photos/` へ移すのが前提。frontmatter の `heroImage` はそのまま、OG 用の `photoVariants` も変更不要）:

```diff
--- a/src/layouts/ArticleLayout.astro
+++ b/src/layouts/ArticleLayout.astro
@@
+import { Image } from 'astro:assets';
 import BaseLayout from './BaseLayout.astro';
@@
 const photo = await photoVariants(heroImage);
+
+// 記事の写真は src/assets/photos に置き、astro:assets で幅別（srcset）に配信する
+const heroModules = import.meta.glob<ImageMetadata>('../assets/photos/*.{avif,jpg,png}', { eager: true, import: 'default' });
+const heroAsset = heroImage ? heroModules[`../assets/photos/${heroImage.split('/').pop()}`] : undefined;
@@
-    {heroImage && (
-      <img
-        src={heroImage}
+    {heroAsset && (
+      <Image
+        src={heroAsset}
         alt={heroImageAlt ?? title}
+        widths={[480, 800, 1200]}
+        sizes="(min-width: 1024px) 992px, calc(100vw - 2rem)"
+        format="avif"
+        quality={60}
+        width={1200}
         loading="eager"
+        fetchpriority="high"
         class:list={['not-prose aspect-video w-full rounded-lg object-cover', ...]}
       />
     )}
-    {heroImage && heroImageCredit && (
+    {heroAsset && heroImageCredit && (
```
結果（実ビルド）: what-is-ultimate の 417KB → 480w 27KB／800w 66KB／1200w 127KB、vs-disc-golf の 600KB → 38／113／253KB、gloves の PNG 465KB → 7KB（イラストなので、目視で劣化がないか確認すること）。移動後は `public/images/photos` から元ファイルを消し、`photoVariants` が見る `public/images/og` はそのまま。

### 4-2. Amazon 商品画像（**中**）
- `AffiliateCard` は 80×80 で表示するが、URL は `_AC_SL1000_`〜`_SL1500_`。実測（全画像のダウンロード量）: accessories 23 枚 **1,926KB**、apparel 12 枚 1,037KB、gloves 2 枚 734KB、shoes 4 枚 303KB、disc 2 枚 331KB。`._AC_SL160_.jpg`（2x 表示用）に差し替えると同じページで 102 / 41 / 14 / 13 / 12KB（約 5%）。
- 注意: 画像URLの改変が Amazon アソシエイトの画像利用条件に合うかは、docs/seo/four-pages-2026-11-24.md の「要確認」にあるとおり未確認。確認できるまでは適用しない。

```diff
--- a/src/components/AffiliateCard.astro
+++ b/src/components/AffiliateCard.astro
@@
 const { name, point, amazonUrl, tier, imageAlt, imageUrl, recommended = false } = Astro.props;
+// 表示は80px。Amazonの画像URLのサイズ指定を160pxに下げる（要：画像利用条件の確認）
+const smallImageUrl = imageUrl?.replace(/\._[^/]*?(\.\w+)?$/, '._AC_SL160_.jpg');
@@
-        src={imageUrl}
+        src={smallImageUrl}
```

### 4-3. キャッシュヘッダー（**中**）
実測（本番）: `/_astro/BaseLayout.BX07h_9v.css` も `/images/photos/*.avif` も `cache-control: public, max-age=0, must-revalidate`（ETag で 304 になるが、毎回往復が発生）。`public/_headers`（Workers Static Assets でも有効）を追加する。作業コピーで `dist/_headers` に出力されることを確認済み。

```diff
+++ b/public/_headers
+/_astro/*
+  Cache-Control: public, max-age=31536000, immutable
+/images/*
+  Cache-Control: public, max-age=86400, stale-while-revalidate=604800
+/favicon.*
+  Cache-Control: public, max-age=86400
```
`/images/*` はファイル名が固定なので、差し替えが即反映されるよう 1 日に抑えた。

### 4-4. スクリプト・フォント（**低**）
- `gtag.js` は 559KB（gzip で約 180KB）の `async` 読み込み。TBT への影響は小さい。同意バナーを設けるときは読み込みの遅延を合わせて検討する。
- `font-family` に日本語フォントの指定がない（`sans-serif` 任せ）。Windows で Meiryo、macOS で Hiragino になり、見た目が環境で変わる。`"Hiragino Sans", "Yu Gothic UI", "Meiryo"` を追加すると揃う。CWV への影響はなし。
- 未圧縮の 42KB CSS が描画をブロックする（gzip で 7.5KB）。現状は許容範囲。
- `/basics/rules` のようなスラッシュなしは 307 で `/…/` に転送される（内部リンクはすべてスラッシュ付きなので影響は外部リンクのみ）。

---

## 5. GA4 の計測

### 5-1. **高**: `internal_nav` と `amazon_link_click` が送信されていない
`define:vars` を付けた `<script>` は Astro が IIFE で囲むため、`function gtag()` は関数内ローカルになる。出力 HTML は `(function(){const GA_MEASUREMENT_ID = "G-…"; … function gtag(){…} …})();`。クリック計測のコードは `typeof window.gtag === 'function'` を条件にしているので、**常に偽**になる。確認: 本番と同じ出力をそのまま Node の `vm` で実行すると `typeof window.gtag === 'undefined'`（修正後は `function`）。また `gtag.js`（559KB）を取得して `window.gtag` の定義がないことも確認した。ページビューは `config` が dataLayer に積まれるため正常に計測されている。

影響: #52（11/10）で入れた `data-nav` の計測、docs/seo/gear-funnel-2026-11-10.md の「施工前後の比較」、プライバシーポリシーの記載（クリックの収集）が、実態は未収集。11/10 以降のイベントは復元できない。**修正後を新しい起点にする**。

```diff
--- a/src/layouts/BaseLayout.astro
+++ b/src/layouts/BaseLayout.astro
@@
           window.dataLayer = window.dataLayer || [];
-          function gtag() { dataLayer.push(arguments); }
-          gtag('js', new Date());
-          gtag('config', GA_MEASUREMENT_ID);
+          // define:vars はIIFEで囲まれるため、window に明示的に公開する
+          window.gtag = function gtag() { window.dataLayer.push(arguments); };
+          window.gtag('js', new Date());
+          window.gtag('config', GA_MEASUREMENT_ID);
```
適用後の確認: GA4 の DebugView（または Chrome の Tag Assistant）で、「次の一歩」のリンクと Amazon リンクをクリックしてイベントが出ること。さらに、GA4 管理画面でイベントスコープのカスタムディメンション `nav`（と下記の追加パラメータ）を登録しないと、レポートでパラメータ別に見られない。

### 5-2. 過不足
**過剰・重複**
- `amazon_link_click` は GA4 の拡張計測（外部リンクの `click` イベント、`outbound=true`）とほぼ重複する。残す価値は、商品名や掲載位置を付けられる点にある。付けないなら、拡張計測だけで足りる。

**不足（優先順）**
1. ヘッダー／フッター／トップのカード／一覧ページのカードのクリック（`data-nav` が「次の一歩」の 5 リンクにしかない）。導線施策の比較対象（ナビ経由の遷移）が取れない。
2. Amazon クリックに商品名・ランク・掲載記事がない。`page_location` はあるが、どのカードかが不明。
3. YouTube の「クリックで再生」（`a[data-yt-embed]`）が未計測。
4. 用語集の一覧 → 個別ページのクリック（§3 の A 案の効果測定に使える）。
5. 本文中の内部リンク（用語リンクなど）。数が多いので、必要になってからでよい。
6. セレクタが `a[href*="amazon.co.jp"]`。将来 `amzn.to` などの短縮URLを使うと取りこぼす。`a[rel~="sponsored"]` が安全。
7. 中ボタン／Ctrl+クリックは `click` に出ない（`auxclick`）。同一タブ遷移の取りこぼしを避けるなら `transport_type: 'beacon'` を付ける。

差分案（ハンドラーを一般化。`data-nav` の命名は `{場所}-{行き先}`）:

```diff
--- a/src/layouts/BaseLayout.astro
+++ b/src/layouts/BaseLayout.astro
@@
     <script>
       document.addEventListener('click', (event) => {
-        const nav = event.target.closest && event.target.closest('a[data-nav]');
-        if (nav && typeof window.gtag === 'function') {
-          window.gtag('event', 'internal_nav', { nav: nav.dataset.nav });
-        }
-        const link = event.target.closest && event.target.closest('a[href*="amazon.co.jp"]');
-        if (link && typeof window.gtag === 'function') {
-          window.gtag('event', 'amazon_link_click', { link_url: link.href });
-        }
+        const el = event.target instanceof Element ? event.target : event.target?.parentElement;
+        if (!el || typeof window.gtag !== 'function') return;
+        const send = (name, params) => window.gtag('event', name, { transport_type: 'beacon', ...params });
+
+        const nav = el.closest('a[data-nav]');
+        if (nav) send('internal_nav', { nav: nav.dataset.nav, dest_path: new URL(nav.href).pathname });
+
+        const aff = el.closest('a[rel~="sponsored"]');
+        if (aff) send('amazon_link_click', { link_url: aff.href, item_name: aff.dataset.item, item_tier: aff.dataset.tier });
+
+        const yt = el.closest('a[data-yt-embed]');
+        if (yt) send('video_play_click', { video_title: yt.dataset.ytTitle });
       });
     </script>
```
```diff
--- a/src/components/AffiliateCard.astro
+++ b/src/components/AffiliateCard.astro
@@
         href={amazonUrl}
         target="_blank"
         rel="sponsored noopener"
+        data-item={name}
+        data-tier={tier}
```
```diff
--- a/src/components/Header.astro
+++ b/src/components/Header.astro
@@ (2か所の NAV_LINKS.map 内の <a>)
-          href={link.href}
+          href={link.href}
+          data-nav={`header-${link.href.split('/')[1]}`}
```
同様に `Footer.astro` は `data-nav={`footer-${link.href.split('/')[1]}`}`、トップと一覧のカードの `<a>` には `data-nav="home-card-…"` / `data-nav="hub-…"` を付ける。**イベントを増やす場合は `/privacy/` の収集項目の表も合わせて更新する**（現状の記載は Amazon クリックと「次の一歩」のみ）。

---

## 6. 対応順の提案

1. §5-1 の 1 行修正（即日。以後のデータが取れる）。
2. §3-4 の用語集一覧の簡素化＋ GSC で 12 用語のカノニカルを確認。
3. §3-5 の `updatedDate` 補正と lastmod 差分（本文の更新日が実態に合う）。
4. §4-3 の `_headers`（リスク最小）→ §4-1 のヒーロー画像（要目視確認）→ §4-2 は Amazon の条件確認後。
5. §5-2 の計測追加（privacy の追記とセット）。
6. 低優先度（OGP 既定サイズ、JSON-LD、リンク追加、description 加筆、薄い用語の加筆）は、通常の記事更新に合わせて。

付記: 検証に使ったスクリプトと作業コピーは作業用ディレクトリのみで、リポジトリには含めていない。`dist/` は監査のため再ビルドしたが `.gitignore` 対象。
