// Phase 3: offline encyclopedias (Kiwix ZIM files) and the user's own library, on ARCA volumes.
import { useCallback, useEffect, useMemo, useState, type FormEvent, type MouseEvent } from "react";

import {
  knowledge,
  library,
  type Article,
  type LibraryDoc,
  type LibraryHit,
  type LibraryStatus,
  type SearchHit,
  type ZimInfo,
} from "../api/engine";
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

const FORMAT_LABEL: Record<LibraryHit["format"], string> = { txt: "Texto", md: "Markdown", html: "HTML", pdf: "PDF" };

/** Snippet with [[word]] markers → text with <mark>, without injecting HTML. */
function Highlighted({ text }: { text: string }) {
  const parts = text.split(/\[\[|\]\]/);
  return <>{parts.map((p, i) => (i % 2 === 1 ? <mark key={i}>{p}</mark> : p))}</>;
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
  const [lib, setLib] = useState<LibraryStatus | null>(null);
  const [docHits, setDocHits] = useState<LibraryHit[] | null>(null);
  const [doc, setDoc] = useState<LibraryDoc | null>(null);

  const loadLibrary = useCallback(async () => {
    try {
      setLib(await library.status());
    } catch (err) {
      setError(errorText(err));
    }
  }, []);

  // While indexing runs in the engine, refresh the progress every second.
  useEffect(() => {
    loadLibrary();
  }, [loadLibrary]);
  useEffect(() => {
    if (!lib?.running) return;
    const timer = window.setInterval(loadLibrary, 1000);
    return () => window.clearInterval(timer);
  }, [lib?.running, loadLibrary]);

  async function indexLibrary() {
    try {
      setLib({ ...(lib ?? { documents: 0, searchable: 0 }), ...(await library.index()) } as LibraryStatus);
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function openDoc(id: number) {
    try {
      setDoc(await library.doc(id));
      setArticle(null);
      setError(null);
    } catch (err) {
      setError(errorText(err));
    }
  }

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
    setDoc(null);
    setHistory([]);
    try {
      const q = query.trim();
      // A chosen encyclopedia narrows the search to it; otherwise search everything.
      const [z, d] = await Promise.all([
        anyAvailable ? knowledge.search(q, zimFilter || null) : Promise.resolve([] as SearchHit[]),
        !zimFilter && (lib?.searchable ?? 0) > 0 ? library.search(q) : Promise.resolve([] as LibraryHit[]),
      ]);
      setHits(z);
      setDocHits(zimFilter ? null : d);
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
      setDoc(null);
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
  const anyAvailable = zims?.some((z) => z.available) ?? false;
  const canSearch = anyAvailable || (lib?.searchable ?? 0) > 0;
  const totalHits = (hits?.length ?? 0) + (docHits?.length ?? 0);

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
                className={`kb-zim${zimFilter === z.id ? " active" : ""}${z.available ? "" : " offline"}`}
                onClick={() => setZimFilter((cur) => (cur === z.id ? "" : z.id))}
                aria-pressed={zimFilter === z.id}
                disabled={!z.available}
              >
                <span className="kb-zim-title">{z.title}</span>
                <span className="muted">
                  {[z.language, `${z.article_count.toLocaleString("pt-BR")} itens`, size(z.size_bytes)]
                    .filter(Boolean)
                    .join(" · ")}
                  {!z.has_fulltext && " · busca só por título"}
                </span>
                {!z.available && (
                  <span className="kb-zim-offline">
                    Disco {z.volume_label ? `“${z.volume_label}” ` : ""}desconectado
                  </span>
                )}
              </button>
              {z.available && (
                <button type="button" className="link-button" onClick={() => open(z.id)}>
                  Página inicial
                </button>
              )}
            </li>
          ))}
        </ul>

        <div className="kb-side-head kb-lib-head">
          <h2>Biblioteca</h2>
          <button
            type="button"
            className="btn btn-outline btn-small"
            onClick={indexLibrary}
            disabled={lib?.running}
            aria-label="Indexar documentos dos volumes"
          >
            <RefreshIcon size={16} /> {lib?.running ? "Indexando…" : "Indexar"}
          </button>
        </div>
        <div className="kb-lib" aria-live="polite">
          {lib?.running ? (
            <>
              <span>
                {lib.done ?? 0} de {lib.total || "?"} arquivos
              </span>
              {lib.current && <span className="muted kb-lib-current">{lib.current}</span>}
              {lib.total ? (
                <div className="meter-bar">
                  <div
                    className="meter-fill"
                    style={{ width: `${((lib.done ?? 0) / lib.total) * 100}%`, background: "var(--accent)" }}
                  />
                </div>
              ) : null}
            </>
          ) : (
            <>
              <span>
                {(lib?.documents ?? 0).toLocaleString("pt-BR")} documento{lib?.documents === 1 ? "" : "s"}
              </span>
              {lib?.last_result && (
                <span className="muted">
                  Última indexação: {lib.last_result.added} novos, {lib.last_result.updated} atualizados,{" "}
                  {lib.last_result.removed} removidos
                  {lib.last_result.failed > 0 && `, ${lib.last_result.failed} com erro`}
                </span>
              )}
              {lib?.error && <span className="kb-zim-offline">{lib.error}</span>}
              {lib?.documents === 0 && (
                <span className="muted">
                  Textos, Markdown, HTML e PDFs dos volumes registrados. PDFs escaneados (só imagem) precisam de OCR,
                  que chega na Fase 6.
                </span>
              )}
            </>
          )}
        </div>
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
                : "Buscar nas enciclopédias e na biblioteca"
            }
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={!canSearch}
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

        {doc ? (
          <article className="kb-reader">
            <div className="kb-reader-head">
              <button type="button" className="link-button" onClick={() => setDoc(null)}>
                Resultados da busca
              </button>
              <span className="muted">
                {FORMAT_LABEL[doc.format]} · {doc.volume_label}
                {!doc.available && " (disco desconectado; texto guardado no índice)"}
              </span>
            </div>
            <h1 className="kb-doc-title">{doc.title}</h1>
            <p className="muted kb-doc-uri">{doc.uri}</p>
            {doc.status !== "ok" ? (
              <p className="kb-external">
                {doc.status === "sem-texto"
                  ? "Este arquivo não tem texto que dê para ler (provavelmente um PDF escaneado; OCR chega na Fase 6)."
                  : "Não foi possível ler este arquivo (danificado, protegido por senha ou grande demais)."}
              </p>
            ) : (
              <div className="kb-doc-text">{doc.text}</div>
            )}
          </article>
        ) : article ? (
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
              {totalHits === 0 ? "Nada encontrado." : `${totalHits} resultado${totalHits > 1 ? "s" : ""}`}
            </p>
            {docHits && docHits.length > 0 && (
              <>
                <h2 className="kb-results-title">Biblioteca</h2>
                <ul>
                  {docHits.map((d) => (
                    <li key={d.id}>
                      <button type="button" className="kb-hit" onClick={() => openDoc(d.id)}>
                        <span className="kb-hit-title">{d.title}</span>
                        <span className="muted kb-hit-zim">
                          {FORMAT_LABEL[d.format]} · {d.volume_label}
                          {!d.available && " · disco desconectado"}
                        </span>
                        {d.snippet && (
                          <span className="kb-hit-snippet">
                            <Highlighted text={d.snippet} />
                          </span>
                        )}
                      </button>
                    </li>
                  ))}
                </ul>
              </>
            )}
            {hits.length > 0 && docHits && docHits.length > 0 && (
              <h2 className="kb-results-title">Enciclopédias</h2>
            )}
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
          (!noZims || (lib?.searchable ?? 0) > 0) && (
            <div className="kb-welcome">
              <h1>Conhecimento</h1>
              <p className="muted">
                Busque nas enciclopédias e nos seus documentos guardados neste computador e nos seus discos. Tudo funciona sem internet.
              </p>
            </div>
          )
        )}
      </section>
    </main>
  );
}
