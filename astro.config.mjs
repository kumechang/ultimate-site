// @ts-check
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import tailwindcss from '@tailwindcss/vite';

const SITE_URL = 'https://ultimate-navi.com';
const CONTENT_DIR = fileURLToPath(new URL('./src/content/', import.meta.url));

// フロントマターの日付（updatedDate、なければ pubDate）を読み取り、URLパス→更新日のMapを作る。
// 記事は pubDate / updatedDate の両方、glossary は updatedDate のみを持つ（無い用語は lastmod を省略する。未確定の日付は入れない）。
// 一覧ページ（/basics/ や /glossary/ など）の lastmod は、配下の記事・用語の最新の日付を使う。
// トップ（/）・/about/・/privacy/ は日付を持たないので lastmod を出さない。
// 日付は本文を直したときに手で更新する運用のため、実際の更新日と離れていないか、ときどき確認する。
const DATED_COLLECTIONS = ['basics', 'gear', 'skills', 'start', 'glossary'];

function buildLastmodMap() {
  const lastmodByPath = new Map();

  for (const collection of DATED_COLLECTIONS) {
    const dir = path.join(CONTENT_DIR, collection);
    if (!fs.existsSync(dir)) continue;

    for (const file of fs.readdirSync(dir)) {
      if (!/\.mdx?$/.test(file)) continue;

      const raw = fs.readFileSync(path.join(dir, file), 'utf-8');
      const frontmatter = raw.match(/^---\n([\s\S]*?)\n---/)?.[1] ?? '';
      if (/^draft:\s*true\s*$/m.test(frontmatter)) continue; // 非公開の記事は、一覧の日付にも含めない
      const updatedDate = frontmatter.match(/^updatedDate:\s*(\S+)/m)?.[1];
      const pubDate = frontmatter.match(/^pubDate:\s*(\S+)/m)?.[1];
      const date = updatedDate ?? pubDate;
      if (!date) continue;

      const slug = file.replace(/\.mdx?$/, '');
      lastmodByPath.set(`/${collection}/${slug}/`, new Date(date));
    }
  }

  // 一覧ページは、配下の最新の日付にする
  for (const collection of DATED_COLLECTIONS) {
    const prefix = `/${collection}/`;
    const times = [...lastmodByPath]
      .filter(([pathname]) => pathname.startsWith(prefix))
      .map(([, date]) => date.getTime());
    if (times.length > 0) lastmodByPath.set(prefix, new Date(Math.max(...times)));
  }

  return lastmodByPath;
}

const lastmodByPath = buildLastmodMap();

export default defineConfig({
  site: SITE_URL,
  integrations: [
    mdx(),
    sitemap({
      serialize(item) {
        const pathname = new URL(item.url).pathname;
        const lastmod = lastmodByPath.get(pathname);
        return lastmod ? { ...item, lastmod } : item;
      },
    }),
  ],
  vite: {
    plugins: [tailwindcss()],
  },
});
