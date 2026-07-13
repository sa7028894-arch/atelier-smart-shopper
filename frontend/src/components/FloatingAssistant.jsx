import { useEffect, useRef, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

function makeSessionId() {
  return crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
}

export default function FloatingAssistant() {
  const [open, setOpen] = useState(false);
  const [sessionId] = useState(makeSessionId);
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Hi! I'm a general AI assistant — ask me anything, not just about products." },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading, open]);

  const handleSend = async (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || isLoading) return;

    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/assistant/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });
      const data = await res.json();
      const replyText = data.error && !data.message ? data.error : data.message;
      setMessages((prev) => [...prev, { role: "assistant", text: replyText }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Couldn't reach the assistant — is the backend running?" },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-3">
      {open && (
        <div className="w-[340px] h-[440px] bg-ink-900 border border-ink-700 rounded-md shadow-2xl flex flex-col overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-ink-700 bg-ink-800/60">
            <div>
              <p className="font-display text-sm text-parchment leading-none">Assistant</p>
              <p className="font-mono text-[9px] tracking-widest text-mute uppercase mt-1">
                General AI · Groq
              </p>
            </div>
            <button
              onClick={() => setOpen(false)}
              aria-label="Close assistant"
              className="text-mute hover:text-parchment text-lg leading-none"
            >
              ×
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-3">
            {messages.map((m, i) => (
              <div
                key={i}
                className={
                  m.role === "user"
                    ? "self-end max-w-[85%] bg-gold-600/15 border border-gold-600/30 text-parchment rounded-sm px-3 py-2 text-xs"
                    : "self-start max-w-[90%] border-l-2 border-gold-500 pl-2.5 text-xs text-parchment/90 leading-relaxed"
                }
              >
                {m.text}
              </div>
            ))}
            {isLoading && (
              <div className="self-start border-l-2 border-gold-500 pl-2.5 text-xs text-mute italic">
                thinking…
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <form onSubmit={handleSend} className="border-t border-ink-700 p-3 flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me anything…"
              className="flex-1 bg-ink-800 border border-ink-600 rounded-sm px-2.5 py-2 text-xs text-parchment placeholder:text-mute/70 focus:border-gold-500 outline-none"
            />
            <button
              type="submit"
              disabled={isLoading}
              className="font-mono text-[10px] uppercase tracking-widest bg-gold-600 hover:bg-gold-500 disabled:opacity-50 text-ink-950 px-3 py-2 rounded-sm transition-colors"
            >
              Send
            </button>
          </form>
        </div>
      )}

      <button
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? "Close assistant" : "Open assistant"}
        className="w-14 h-14 rounded-full bg-gold-600 hover:bg-gold-500 text-ink-950 shadow-xl flex items-center justify-center transition-colors"
      >
        {open ? (
          <span className="text-2xl leading-none">×</span>
        ) : (
          <span className="font-display text-lg leading-none">AI</span>
        )}
      </button>
    </div>
  );
}
