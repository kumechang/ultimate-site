import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const articleSchema = z.object({
  title: z.string(),
  description: z.string(),
  pubDate: z.coerce.date(),
  updatedDate: z.coerce.date().optional(),
  order: z.number().default(0),
  draft: z.boolean().default(false),
  heroImage: z.string().optional(),
  heroImageAlt: z.string().optional(),
});

const basics = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/basics' }),
  schema: articleSchema,
});

const gear = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/gear' }),
  schema: articleSchema.extend({
    // アフィリエイトリンクを含む記事であることを明示するフラグ
    hasAffiliateLinks: z.boolean().default(true),
  }),
});

const skills = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/skills' }),
  schema: articleSchema,
});

const start = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/start' }),
  schema: articleSchema,
});

const glossary = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/glossary' }),
  schema: z.object({
    term: z.string(),
    reading: z.string().optional(),
    description: z.string().optional(),
    order: z.number().default(0),
  }),
});

export const collections = { basics, gear, skills, start, glossary };
