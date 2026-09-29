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

// pubDate/updatedDateをフロントマターから読み取り、URLパス→更新日のMapを作る。
// glossaryには日付フィールドがないため対象外（lastmodは未確定の日付を入れるより省略する）。
const DATED_COLLECTIONS = ['basics', 'gear', 'skills', 'start'];

function buildLastmodMap() {
  const lastmodByPath = new Map();

  for (const collection of DATED_COLLECTIONS) {
    const dir = path.join(CONTENT_DIR, collection);
    if (!fs.existsSync(dir)) continue;

    for (const file of fs.readdirSync(dir)) {
      if (!/\.mdx?$/.test(file)) continue;

      const raw = fs.readFileSync(path.join(dir, file), 'utf-8');
      const frontmatter = raw.match(/^---\n([\s\S]*?)\n---/)?.[1] ?? '';
      const updatedDate = frontmatter.match(/^updatedDate:\s*(\S+)/m)?.[1];
      const pubDate = frontmatter.match(/^pubDate:\s*(\S+)/m)?.[1];
      const date = updatedDate ?? pubDate;
      if (!date) continue;

      const slug = file.replace(/\.mdx?$/, '');
      lastmodByPath.set(`/${collection}/${slug}/`, new Date(date));
    }
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
