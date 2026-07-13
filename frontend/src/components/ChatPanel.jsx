import { useEffect, useRef, useState } from "react";

export default function ChatPanel({ messages, onSend, isLoading }) {
  const [input, setInput] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setInput("");
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-5 py-6 flex flex-col gap-4">
        {messages.map((m, i) => (
          <div
            key={i}
            className={
              m.role === "user"
                ? "self-end max-w-[85%] bg-gold-600/15 border border-gold-600/30 text-parchment rounded-sm px-4 py-2.5 text-sm"
                : "self-start max-w-[90%] border-l-2 border-gold-500 pl-3 text-sm text-parchment/90 leading-relaxed"
            }
          >
            {m.text}
          </div>
        ))}
        {isLoading && (
          <div className="self-start border-l-2 border-gold-500 pl-3 text-sm text-mute italic">
            thinking…
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="border-t border-ink-700 p-4 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Tell me what you're shopping for…"
          className="flex-1 bg-ink-800 border border-ink-600 rounded-sm px-3 py-2.5 text-sm text-parchment placeholder:text-mute/70 focus:border-gold-500 outline-none"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="font-mono text-xs uppercase tracking-widest bg-gold-600 hover:bg-gold-500 disabled:opacity-50 text-ink-950 px-4 py-2.5 rounded-sm transition-colors"
        >
          Send
        </button>
      </form>
    </div>
  );
}
