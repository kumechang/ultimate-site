// public/images/photos の写真から、検索結果・SNS共有用のJPEG（16:9 / 4:3 / 1:1）を public/images/og に作る。
// og:image と Article の構造化データ(image)で使う。AVIFは共有プレビューで読まれないことがあるためJPEGにする。
// 使い方: node scripts/images/make_og_images.mjs   （写真を追加・差し替えたときに再実行し、生成物をコミットする）
import { readdir, mkdir } from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';

const SRC = 'public/images/photos';
// 記事の内容と合わない写真（費用の記事のサッカー写真）は、検索結果用の画像を作らない
const SKIP = new Set(['cleats-01']);
const OUT = 'public/images/og';
const RATIOS = { '16x9': [16, 9], '4x3': [4, 3], '1x1': [1, 1] };
const MAX_WIDTH = 1200;

await mkdir(OUT, { recursive: true });
for (const file of (await readdir(SRC)).sort()) {
  const base = path.parse(file).name;
  if (SKIP.has(base)) continue;
  const { width, height } = await sharp(path.join(SRC, file)).metadata();
  for (const [name, [rw, rh]] of Object.entries(RATIOS)) {
    // 元画像に収まる最大の矩形（拡大はしない）を、幅1200px以下で切り出す
    const w = Math.min(MAX_WIDTH, width, Math.floor((height * rw) / rh));
    const h = Math.round((w * rh) / rw);
    const dest = path.join(OUT, `${base}-${name}.jpg`);
    await sharp(path.join(SRC, file))
      .resize(w, h, { fit: 'cover', position: sharp.strategy.attention })
      .jpeg({ quality: 80, mozjpeg: true })
      .toFile(dest);
    console.log(dest, `${w}x${h}`);
  }
}
