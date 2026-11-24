// 「## Q. 質問」見出し＋回答の形で書かれた Markdown から、FAQPage の構造化データ用の質問と回答を取り出す。
// 画面に出ている文章をそのまま使うことで、本文と構造化データの二重管理（食い違い）を避ける。
export interface FaqItem {
  question: string;
  answer: string;
}

const plain = (md: string) =>
  md
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1') // [文字](URL) → 文字
    .replace(/\*\*|__|`/g, '')
    .replace(/^\s*A\.\s*/, '') // 回答の先頭の「A.」
    .replace(/\s*\n\s*/g, ' ')
    .replace(/([。！？]) +/g, '$1')
    .trim();

export function faqFromMarkdown(body: string | undefined): FaqItem[] {
  if (!body) return [];
  return body
    .split(/^## Q\.\s*/m)
    .slice(1)
    .map((block) => {
      const [question, ...rest] = block.split('\n');
      return { question: plain(question), answer: plain(rest.join('\n')) };
    })
    .filter((item) => item.question && item.answer);
}
