import { useState } from "react";
import ChatPanel from "./components/ChatPanel";
import ProductCard from "./components/ProductCard";
import FloatingAssistant from "./components/FloatingAssistant";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

function makeSessionId() {
  return crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
}

export default function App() {
  const [sessionId] = useState(makeSessionId);
  const [messages, setMessages] = useState([
    {
      role: "agent",
      text: "Hi, I'm your personal shopper. Tell me what you're looking for — a category, an occasion, or just a vague idea — and I'll find matches from the catalog.",
    },
  ]);
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async (text) => {
    setMessages((prev) => [...prev, { role: "user", text }]);
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "agent", text: data.message }]);
      if (data.type === "recommendations") {
        setProducts(data.products);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "agent", text: "I couldn't reach the recommendation service. Is the backend running?" },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen text-parchment font-sans flex flex-col">
      <header className="border-b border-ink-700 px-6 py-5 flex items-baseline justify-between">
        <div>
          <h1 className="font-display text-2xl tracking-tight">Atelier</h1>
          <p className="text-xs text-mute font-mono tracking-widest uppercase mt-0.5">
            Personal Shopper Agent
          </p>
        </div>
        <span className="text-xs text-mute font-mono">GenAI Course Project · Team 10</span>
      </header>

      <main className="flex-1 grid grid-cols-1 lg:grid-cols-[380px_1fr]">
        <section className="border-r border-ink-700 h-[calc(100vh-77px)] lg:sticky lg:top-0">
          <ChatPanel messages={messages} onSend={handleSend} isLoading={isLoading} />
        </section>

        <section className="p-6 overflow-y-auto">
          {products.length === 0 ? (
            <div className="h-full flex items-center justify-center text-center">
              <p className="text-mute text-sm max-w-xs">
                Recommendations will appear here once you describe what you need.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {products.map((p) => (
                <ProductCard key={p.id} product={p} />
              ))}
            </div>
          )}
        </section>
      </main>

      <FloatingAssistant />
    </div>
  );
}
