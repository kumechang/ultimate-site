import { existsSync } from 'node:fs';
import sharp from 'sharp';

// scripts/images/make_og_images.mjs が public/images/og に作る、写真ごとのJPEG（16:9 / 4:3 / 1:1）を探す。
// 検索結果のサムネイルやSNS共有用。見つからない写真（未生成）は空を返し、呼び出し側は既定の画像を使う。
export interface PhotoVariants {
  urls: string[];
  og?: { url: string; width: number; height: number };
}

const RATIOS = ['16x9', '4x3', '1x1'];

export async function photoVariants(heroImage?: string): Promise<PhotoVariants> {
  const base = heroImage?.match(/^\/images\/photos\/([^/.]+)\.\w+$/)?.[1];
  if (!base) return { urls: [] };
  const urls = RATIOS.map((r) => `/images/og/${base}-${r}.jpg`).filter((u) => existsSync(`public${u}`));
  const ogUrl = urls.find((u) => u.endsWith('-16x9.jpg'));
  if (!ogUrl) return { urls };
  const { width, height } = await sharp(`public${ogUrl}`).metadata();
  return { urls, og: width && height ? { url: ogUrl, width, height } : undefined };
}
