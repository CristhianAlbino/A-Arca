// Renders model output safely: plain text with paragraphs and ``` code blocks.
// No HTML from the model is ever injected. (Full Markdown with react-markdown is a
// Phase 2 follow-up; see FASE-02.md.)
import { useState } from "react";

interface Block {
  kind: "text" | "code";
  content: string;
  lang?: string;
}

export function splitBlocks(text: string): Block[] {
  const blocks: Block[] = [];
  const parts = text.split(/```/);
  parts.forEach((part, i) => {
    if (i % 2 === 1) {
      const newline = part.indexOf("\n");
      const lang = newline > 0 ? part.slice(0, newline).trim() : "";
      blocks.push({ kind: "code", lang, content: newline > 0 ? part.slice(newline + 1) : part });
    } else if (part.trim()) {
      blocks.push({ kind: "text", content: part.trim() });
    }
  });
  return blocks;
}

function CodeBlock({ code, lang }: { code: string; lang?: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="code-block">
      <div className="code-head">
        <span>{lang || "código"}</span>
        <button
          type="button"
          onClick={async () => {
            await navigator.clipboard?.writeText(code);
            setCopied(true);
            window.setTimeout(() => setCopied(false), 1500);
          }}
        >
          {copied ? "Copiado" : "Copiar"}
        </button>
      </div>
      <pre>
        <code>{code}</code>
      </pre>
    </div>
  );
}

export function MessageText({ text }: { text: string }) {
  return (
    <>
      {splitBlocks(text).map((b, i) =>
        b.kind === "code" ? (
          <CodeBlock key={i} code={b.content} lang={b.lang} />
        ) : (
          <p key={i} className="msg-text">
            {b.content}
          </p>
        ),
      )}
    </>
  );
}
