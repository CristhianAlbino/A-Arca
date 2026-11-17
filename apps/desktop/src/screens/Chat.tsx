import { useCallback, useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { ai, type AiStatus, type ChatEvent, type ConversationSummary } from "../api/engine";
import { ArcaMark, PlusIcon } from "../components/Icons";
import { MessageText } from "../components/MessageText";
import { gb } from "../format";

interface UiMessage {
  key: string;
  role: "user" | "assistant";
  content: string;
  status: "ok" | "streaming" | "interrupted" | "error";
  stats?: Record<string, number | null> | null;
}

let keySeq = 0;
const nextKey = () => `m${++keySeq}`;

function groupLabel(iso: string): string {
  const day = 24 * 60 * 60 * 1000;
  const date = new Date(iso);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  if (date >= today) return "Hoje";
  if (date.getTime() >= today.getTime() - day) return "Ontem";
  if (date.getTime() >= today.getTime() - 7 * day) return "Últimos 7 dias";
  return "Mais antigas";
}

export function Chat() {
  const [status, setStatus] = useState<AiStatus | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const [model, setModel] = useState<string>("");
  const [input, setInput] = useState("");
  const [search, setSearch] = useState("");
  const [streaming, setStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);

  const refreshStatus = useCallback(async () => {
    try {
      const st = await ai.status();
      setStatus(st);
      setStatusError(null);
      setModel((current) => {
        if (current && st.models.some((m) => m.name === current)) return current;
        return st.default_model ?? st.loaded[0]?.name ?? st.models[0]?.name ?? "";
      });
    } catch (err) {
      setStatusError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  const refreshConversations = useCallback(async () => {
    try {
      setConversations(await ai.conversations());
    } catch {
      /* the banner from refreshStatus already explains connection problems */
    }
  }, []);

  useEffect(() => {
    refreshStatus();
    refreshConversations();
  }, [refreshStatus, refreshConversations]);

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ block: "end" });
  }, [messages]);

  async function openConversation(id: string) {
    if (streaming) return;
    const conv = await ai.conversation(id);
    setCurrentId(conv.id);
    setNotice(null);
    if (conv.model) setModel(conv.model);
    setMessages(
      conv.messages
        .filter((m) => m.role !== "system")
        .map((m) => ({
          key: `db${m.id}`,
          role: m.role as "user" | "assistant",
          content: m.content,
          status: m.status,
          stats: m.stats,
        })),
    );
  }

  function newConversation() {
    if (streaming) return;
    setCurrentId(null);
    setMessages([]);
    setNotice(null);
  }

  async function removeConversation(id: string) {
    if (!window.confirm("Apagar esta conversa deste computador?")) return;
    await ai.deleteConversation(id);
    if (id === currentId) newConversation();
    refreshConversations();
  }

  function updateLast(change: (m: UiMessage) => UiMessage) {
    setMessages((list) => list.map((m, i) => (i === list.length - 1 ? change(m) : m)));
  }

  async function send() {
    const text = input.trim();
    if (!text || !model || streaming) return;
    setInput("");
    setNotice(null);
    setMessages((list) => [
      ...list,
      { key: nextKey(), role: "user", content: text, status: "ok" },
      { key: nextKey(), role: "assistant", content: "", status: "streaming" },
    ]);
    setStreaming(true);
    const controller = new AbortController();
    abortRef.current = controller;

    const onEvent = (event: ChatEvent) => {
      switch (event.type) {
        case "meta":
          setCurrentId(event.conversation_id);
          break;
        case "notice":
          setNotice(event.message);
          break;
        case "delta":
          updateLast((m) => ({ ...m, content: m.content + event.text }));
          break;
        case "done":
          updateLast((m) => ({ ...m, status: "ok", stats: event.stats }));
          break;
        case "error":
          updateLast((m) => ({ ...m, status: "error", content: m.content || event.message }));
          break;
      }
    };

    try {
      await ai.chat({ text, model, conversation_id: currentId }, onEvent, controller.signal);
    } catch (err) {
      if (controller.signal.aborted) {
        updateLast((m) => ({ ...m, status: "interrupted" }));
      } else {
        const message = err instanceof Error ? err.message : String(err);
        updateLast((m) => ({ ...m, status: "error", content: m.content || message }));
      }
    } finally {
      setStreaming(false);
      abortRef.current = null;
      refreshConversations();
      refreshStatus();
    }
  }

  function stop() {
    abortRef.current?.abort();
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  const groups = useMemo(() => {
    const filtered = conversations.filter((c) => c.title.toLowerCase().includes(search.trim().toLowerCase()));
    const out: { label: string; items: ConversationSummary[] }[] = [];
    for (const c of filtered) {
      const label = groupLabel(c.updated_at);
      const group = out.find((g) => g.label === label);
      if (group) group.items.push(c);
      else out.push({ label, items: [c] });
    }
    return out;
  }, [conversations, search]);

  const available = status?.available ?? false;
  const selected = status?.models.find((m) => m.name === model);
  const loadedNow = status?.loaded.find((m) => m.name === model);

  return (
    <div className="chat">
      <aside className="chat-side" aria-label="Conversas">
        <button type="button" className="btn btn-outline" onClick={newConversation} disabled={streaming}>
          <PlusIcon /> Nova conversa
        </button>
        <label className="sr-only" htmlFor="busca-conversas">
          Buscar conversas
        </label>
        <input
          id="busca-conversas"
          className="chat-search"
          type="search"
          placeholder="Buscar conversas"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <nav aria-label="Histórico" className="chat-history">
          {groups.length === 0 && <p className="muted chat-empty-list">Nenhuma conversa ainda.</p>}
          {groups.map((g) => (
            <div key={g.label}>
              <span className="chat-group">{g.label}</span>
              {g.items.map((c) => (
                <div key={c.id} className={`chat-item${c.id === currentId ? " active" : ""}`}>
                  <button type="button" className="chat-item-open" onClick={() => openConversation(c.id)}>
                    {c.title}
                  </button>
                  <button
                    type="button"
                    className="chat-item-delete"
                    aria-label={`Apagar conversa: ${c.title}`}
                    onClick={() => removeConversation(c.id)}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          ))}
        </nav>
        <div className="chat-side-foot">
          <span className="pill pill-ok">
            <span className="dot" />
            OFFLINE · tudo local
          </span>
          <span>As conversas ficam só neste computador.</span>
        </div>
      </aside>

      <section className="chat-main" aria-label="Conversa">
        <div className="chat-top">
          <label className="sr-only" htmlFor="modelo">
            Modelo
          </label>
          <select
            id="modelo"
            className="model-select"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            disabled={!available || streaming}
          >
            {!status?.models.length && <option value="">Nenhum modelo instalado</option>}
            {status?.models.map((m) => (
              <option key={m.name} value={m.name}>
                {m.name} {m.parameter_size ? `· ${m.parameter_size}` : ""} · {gb(m.size_bytes)}
              </option>
            ))}
          </select>
          <span className="pill pill-ok">LOCAL</span>
          <span className="muted chat-model-state">
            {loadedNow ? "carregado na memória" : selected ? "carrega ao enviar" : ""}
          </span>
        </div>

        {(statusError || (status && !status.available)) && (
          <div className="banner" role="alert">
            {statusError ?? status?.reason}
          </div>
        )}
        {status?.available && status.models.length === 0 && (
          <div className="banner" role="alert">
            O Ollama está aberto, mas nenhum modelo foi instalado ainda. O download de modelos chega na
            etapa 2B; por enquanto, use <code>ollama pull</code> no terminal.
          </div>
        )}

        <div className="chat-scroll">
          <div className="chat-column">
            {messages.length === 0 ? (
              <div className="chat-welcome">
                <span className="chat-avatar big">
                  <ArcaMark size={28} color="var(--accent-ink)" />
                </span>
                <h1>Como posso ajudar?</h1>
                <p className="muted">
                  A conversa roda no seu computador, com o modelo escolhido acima. Nesta versão a IA ainda
                  não consulta a sua biblioteca de documentos.
                </p>
              </div>
            ) : (
              messages.map((m) =>
                m.role === "user" ? (
                  <div key={m.key} className="msg-user">
                    {m.content}
                  </div>
                ) : (
                  <div key={m.key} className="msg-assistant">
                    <span className="chat-avatar">
                      <ArcaMark size={18} color="var(--accent-ink)" />
                    </span>
                    <div className={`msg-body${m.status === "error" ? " msg-error" : ""}`}>
                      {m.content ? <MessageText text={m.content} /> : m.status === "streaming" && <span className="typing">Pensando…</span>}
                      {m.status === "interrupted" && <span className="msg-meta">Resposta interrompida.</span>}
                      {m.status === "ok" && m.stats?.tokens_per_second != null && (
                        <span className="msg-meta">
                          {m.stats.output_tokens} tokens · {m.stats.tokens_per_second} tokens/s
                        </span>
                      )}
                    </div>
                  </div>
                ),
              )
            )}
            {notice && <p className="chat-notice">{notice}</p>}
            <div ref={endRef} />
          </div>
        </div>

        <div className="composer-wrap">
          <div className="composer">
            <label className="sr-only" htmlFor="mensagem">
              Mensagem para a ARCA
            </label>
            <textarea
              id="mensagem"
              rows={1}
              placeholder={available ? "Pergunte qualquer coisa à ARCA" : "IA local indisponível"}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              disabled={!available || !model}
            />
            {streaming ? (
              <button type="button" className="composer-btn" aria-label="Parar resposta" onClick={stop}>
                <span className="stop-square" />
              </button>
            ) : (
              <button
                type="button"
                className="composer-btn"
                aria-label="Enviar mensagem"
                onClick={send}
                disabled={!input.trim() || !model || !available}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M12 19V5M5 12l7-7 7 7" />
                </svg>
              </button>
            )}
          </div>
          <p className="composer-hint">
            Modo offline: perguntas e respostas não saem deste computador. A IA pode errar; confira o que for
            importante.
          </p>
        </div>
      </section>
    </div>
  );
}
