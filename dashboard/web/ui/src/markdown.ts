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
  let listOpen = false;

  const closeList = () => {
    if (listOpen) {
      parts.push("</ul>");
      listOpen = false;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i] ?? "";
    if (/^\s*```/.test(line)) {
      closeList();
      const code: string[] = [];
      i += 1;
      while (i < lines.length && !/^\s*```/.test(lines[i] ?? "")) {
        code.push(lines[i] ?? "");
        i += 1;
      }
      parts.push(`<pre>${esc(code.join("\n"))}</pre>`);
      continue;
    }
    if (/^##\s+/.test(line)) {
      closeList();
      parts.push(`<h4>${esc(line.replace(/^##\s+/, ""))}</h4>`);
      continue;
    }
    if (/^[-*]\s+/.test(line)) {
      if (!listOpen) {
        parts.push("<ul>");
        listOpen = true;
      }
      parts.push(`<li>${inline(line.replace(/^[-*]\s+/, ""), ctx)}</li>`);
      continue;
    }
    if (!line.trim()) {
      closeList();
      continue;
    }
    closeList();
    parts.push(`<p>${inline(line, ctx)}</p>`);
  }
  closeList();
  return parts.join("");
}
