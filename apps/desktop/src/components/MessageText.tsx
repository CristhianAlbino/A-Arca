// Renders model output as Markdown (GFM: tables, lists, strikethrough, task lists).
// Safe by default: react-markdown never renders raw HTML from the model, and links
// open nothing inside the app window (offline first: they are shown, not followed).
import { useState, type ReactNode } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

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

function textOf(node: ReactNode): string {
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(textOf).join("");
  return "";
}

const components: Components = {
  // Fenced blocks arrive as <pre><code class="language-x">; inline code stays <code>.
  pre({ children }) {
    const child = Array.isArray(children) ? children[0] : children;
    const props = (child as { props?: { className?: string; children?: ReactNode } } | null)?.props ?? {};
    const lang = /language-([\w+-]+)/.exec(props.className ?? "")?.[1];
    return <CodeBlock code={textOf(props.children).replace(/\n$/, "")} lang={lang} />;
  },
  a({ href, children }) {
    // No navigation from inside the app: show where the link points instead.
    return (
      <span className="msg-link" title={href}>
        {children}
      </span>
    );
  },
  img({ alt }) {
    // Remote images would be network requests; show the description only.
    return <span className="muted">[imagem: {alt || "sem descrição"}]</span>;
  },
  table({ children }) {
    return (
      <div className="msg-table">
        <table>{children}</table>
      </div>
    );
  },
};

export function MessageText({ text }: { text: string }) {
  return (
    <div className="msg-md">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {text}
      </ReactMarkdown>
    </div>
  );
}
