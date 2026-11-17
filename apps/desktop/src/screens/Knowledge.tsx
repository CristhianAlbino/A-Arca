// Phase 3: offline encyclopedias (Kiwix ZIM files on ARCA volumes).
import { useCallback, useEffect, useMemo, useState, type FormEvent, type MouseEvent } from "react";

import { knowledge, type Article, type SearchHit, type ZimInfo } from "../api/engine";
import { RefreshIcon } from "../components/Icons";
import { size } from "../format";

const BLOCKED_TAGS = "script,style,iframe,object,embed,form,link,meta,base,noscript,template";

/** Second cleaning pass in the browser (the engine already cleans): no scripts, no handlers. */
function sanitize(html: string): string {
  const doc = new DOMParser().parseFromString(`<div>${html}</div>`, "text/html");
  doc.querySelectorAll(BLOCKED_TAGS).forEach((el) => el.remove());
  doc.querySelectorAll("*").forEach((el) => {
    for (const attr of [...el.attributes]) {
      const name = attr.name.toLowerCase();
      const value = attr.value.trim().toLowerCase();
      if (name.startsWith("on") || name === "style" || name === "srcset") el.removeAttribute(attr.name);
      if ((name === "href" || name === "src") && !value.startsWith("#") && !value.startsWith("data:image/")) {
        el.removeAttribute(attr.name);
      }
    }
  });
  return doc.body.firstElementChild?.innerHTML ?? "";
}

function errorText(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}

export function Knowledge() {
  const [zims, setZims] = useState<ZimInfo[] | null>(null);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [zimFilter, setZimFilter] = useState<string>("");
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [article, setArticle] = useState<Article | null>(null);
  const [history, setHistory] = useState<Article[]>([]);
  const [external, setExternal] = useState<string | null>(null);

  const loadZims = useCallback(async (rescan: boolean) => {
    setScanning(true);
    try {
      setZims(await knowledge.zims(rescan));
      setError(null);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setScanning(false);
    }
  }, []);

  useEffect(() => {
    loadZims(false);
  }, [loadZims]);

  async function search(e: FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setArticle(null);
    setHistory([]);
    try {
      setHits(await knowledge.search(query.trim(), zimFilter || null));
      setError(null);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setSearching(false);
    }
  }

  async function open(zimId: string, path?: string | null, keepHistory = false) {
    try {
      const next = await knowledge.article(zimId, path);
      if (keepHistory && article) setHistory((h) => [...h, article]);
      else if (!keepHistory) setHistory([]);
      setArticle(next);
      setExternal(null);
      setError(null);
      document.querySelector(".kb-reader")?.scrollTo?.({ top: 0 });
    } catch (err) {
      setError(errorText(err));
    }
  }

  function back() {
    const prev = history[history.length - 1];
    setHistory((h) => h.slice(0, -1));
    setArticle(prev ?? null);
    setExternal(null);
  }

  function onArticleClick(e: MouseEvent<HTMLDivElement>) {
    const link = (e.target as HTMLElement).closest("a");
    if (!link || !article) return;
    const internal = link.getAttribute("data-zim-path");
    const outside = link.getAttribute("data-external");
    if (internal) {
      e.preventDefault();
      open(article.zim_id, internal, true);
    } else if (outside) {
      e.preventDefault();
      setExternal(outside);
    }
  }

  const cleanHtml = useMemo(() => (article ? sanitize(article.html) : ""), [article]);
  const noZims = zims !== null && zims.length === 0;

  return (
    <main className="kb">
      <aside className="kb-side" aria-label="Enciclopédias">
        <div className="kb-side-head">
          <h2>Enciclopédias</h2>
          <button
            type="button"
            className="btn btn-outline btn-small"
            onClick={() => loadZims(true)}
            disabled={scanning}
            aria-label="Procurar enciclopédias nos volumes"
          >
            <RefreshIcon size={16} /> {scanning ? "Procurando…" : "Procurar"}
          </button>
        </div>
        {noZims && (
          <div className="kb-empty">
            <p>Nenhuma enciclopédia encontrada nos volumes conectados.</p>
            <ol>
              <li>Baixe arquivos .zim (Wikipédia, WikiMed, Wikibooks…) no site do Kiwix enquanto tiver internet.</li>
              <li>
                Coloque-os num volume registrado na tela Início, por exemplo em <code>03_ENCICLOPEDIAS</code>.
              </li>
              <li>Clique em “Procurar”.</li>
            </ol>
          </div>
        )}
        <ul className="kb-zims">
          {zims?.map((z) => (
            <li key={z.id}>
              <button
                type="button"
                className={`kb-zim${zimFilter === z.id ? " active" : ""}`}
                onClick={() => setZimFilter((cur) => (cur === z.id ? "" : z.id))}
                aria-pressed={zimFilter === z.id}
              >
                <span className="kb-zim-title">{z.title}</span>
                <span className="muted">
                  {[z.language, `${z.article_count.toLocaleString("pt-BR")} itens`, size(z.size_bytes)]
                    .filter(Boolean)
                    .join(" · ")}
                  {!z.has_fulltext && " · busca só por título"}
                </span>
              </button>
              <button type="button" className="link-button" onClick={() => open(z.id)}>
                Página inicial
              </button>
            </li>
          ))}
        </ul>
      </aside>

      <section className="kb-main" aria-label="Busca e leitura">
        <form className="kb-search" onSubmit={search} role="search">
          <label className="sr-only" htmlFor="kb-q">
            Buscar nas enciclopédias
          </label>
          <input
            id="kb-q"
            className="chat-search"
            type="search"
            placeholder={
              zimFilter
                ? `Buscar em ${zims?.find((z) => z.id === zimFilter)?.title ?? "enciclopédia"}`
                : "Buscar em todas as enciclopédias"
            }
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={!zims?.length}
          />
          <button type="submit" className="btn btn-primary btn-small" disabled={!query.trim() || searching}>
            {searching ? "Buscando…" : "Buscar"}
          </button>
        </form>

        {error && (
          <div className="banner" role="alert">
            {error}
          </div>
        )}

        {article ? (
          <article className="kb-reader">
            <div className="kb-reader-head">
              {history.length > 0 && (
                <button type="button" className="btn btn-secondary btn-small" onClick={back}>
                  ← Voltar
                </button>
              )}
              {hits && (
                <button type="button" className="link-button" onClick={() => setArticle(null)}>
                  Resultados da busca
                </button>
              )}
              <span className="muted">{article.zim_title}</span>
            </div>
            {external && (
              <p className="kb-external" role="status">
                Link para fora da ARCA (não abre offline): <code>{external}</code>
              </p>
            )}
            <div className="kb-article" onClick={onArticleClick} dangerouslySetInnerHTML={{ __html: cleanHtml }} />
          </article>
        ) : hits ? (
          <div className="kb-results">
            <p className="muted">
              {hits.length === 0 ? "Nada encontrado." : `${hits.length} resultado${hits.length > 1 ? "s" : ""}`}
            </p>
            <ul>
              {hits.map((h) => (
                <li key={`${h.zim_id}/${h.path}`}>
                  <button type="button" className="kb-hit" onClick={() => open(h.zim_id, h.path)}>
                    <span className="kb-hit-title">{h.title}</span>
                    <span className="muted kb-hit-zim">{h.zim_title}</span>
                    {h.snippet && <span className="kb-hit-snippet">{h.snippet}</span>}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          !noZims && (
            <div className="kb-welcome">
              <h1>Conhecimento</h1>
              <p className="muted">
                Busque nas enciclopédias guardadas neste computador e nos seus discos. Tudo funciona sem internet.
              </p>
            </div>
          )
        )}
      </section>
    </main>
  );
}
