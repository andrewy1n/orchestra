/**
 * Small markdown renderer matching the dashboard spike:
 * headings (##), lists, fenced code, **bold**, `code`.
 * Optional deep-link context linkifies known reference tokens.
 */

import { linkifyText, type RefContext } from "./links";

function esc(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function plain(text: string, ctx?: RefContext | null): string {
  if (ctx) return linkifyText(text, ctx, esc);
  return esc(text);
}

function inline(text: string, ctx?: RefContext | null): string {
  const re = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let last = 0;
  let out = "";
  let match: RegExpExecArray | null;
  while ((match = re.exec(text))) {
    if (match.index > last) out += plain(text.slice(last, match.index), ctx);
    const tok = match[0];
    if (tok.startsWith("**")) {
      out += `<strong>${esc(tok.slice(2, -2))}</strong>`;
    } else {
      out += `<code>${esc(tok.slice(1, -1))}</code>`;
    }
    last = match.index + tok.length;
  }
  if (last < text.length) out += plain(text.slice(last), ctx);
  return out;
}

/** Render a markdown-ish body to HTML for `{@html}` in the overlay. */
export function renderMarkdown(
  src: string,
  ctx?: RefContext | null,
): string {
  const lines = (src || "").split("\n");
  const parts: string[] = [];
  let listTag: "ul" | "ol" | null = null;
  let item: string[] = [];

  const closeItem = () => {
    if (!item.length) return;
    parts.push(`<li>${inline(item.join(" "), ctx)}</li>`);
    item = [];
  };

  const closeList = () => {
    closeItem();
    if (listTag) {
      parts.push(`</${listTag}>`);
      listTag = null;
    }
  };

  const openList = (tag: "ul" | "ol") => {
    if (listTag && listTag !== tag) closeList();
    if (!listTag) {
      parts.push(`<${tag}>`);
      listTag = tag;
    }
  };

  const paragraph: string[] = [];
  const flushParagraph = () => {
    if (!paragraph.length) return;
    parts.push(`<p>${inline(paragraph.join(" "), ctx)}</p>`);
    paragraph.length = 0;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i] ?? "";
    if (/^\s*```/.test(line)) {
      closeList();
      flushParagraph();
      const code: string[] = [];
      i += 1;
      while (i < lines.length && !/^\s*```/.test(lines[i] ?? "")) {
        code.push(lines[i] ?? "");
        i += 1;
      }
      parts.push(`<pre><code>${esc(code.join("\n"))}</code></pre>`);
      continue;
    }
    const heading = /^(#{1,3})\s+(.+)$/.exec(line);
    if (heading) {
      closeList();
      flushParagraph();
      const tag = heading[1].length === 1 ? "h3" : "h4";
      parts.push(`<${tag}>${esc(heading[2])}</${tag}>`);
      continue;
    }
    const bullet = /^[-*]\s+(.+)$/.exec(line);
    if (bullet) {
      flushParagraph();
      openList("ul");
      closeItem();
      item.push(bullet[1] ?? "");
      continue;
    }
    const numbered = /^\d+[.)]\s+(.+)$/.exec(line);
    if (numbered) {
      flushParagraph();
      openList("ol");
      closeItem();
      item.push(numbered[1] ?? "");
      continue;
    }
    if (listTag && /^\s+\S/.test(line)) {
      item.push(line.trim());
      continue;
    }
    if (!line.trim()) {
      closeList();
      flushParagraph();
      continue;
    }
    closeList();
    paragraph.push(line.trim());
  }
  closeList();
  flushParagraph();
  return parts.join("");
}
