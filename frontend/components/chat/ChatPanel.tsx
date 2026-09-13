"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, BookmarkPlus, BookOpen, Sparkles, User, Loader2, Check } from "lucide-react";
import { authFetch } from "@/lib/auth";

interface SourceCitation {
  chunk_id: string;
  page?: number;
  chapter?: string;
  snippet: string;
  relevance_score?: number;
}

interface MessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceCitation[];
}

interface ChatPanelProps {
  bookId: string;
  onNavigateToPage: (page: number) => void;
  onSavedToNotes?: () => void;
}

export default function ChatPanel({ bookId, onNavigateToPage, onSavedToNotes }: ChatPanelProps) {
  const [messages, setMessages] = useState<MessageItem[]>([
    {
      id: "intro",
      role: "assistant",
      content: "Hello! I am your AI assistant for this book. Ask me anything about its chapters, core thesis, or specific concepts. Every answer is grounded in exact page citations.",
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [savedNotes, setSavedNotes] = useState<Record<string, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputValue.trim() || loading) return;

    const userQuery = inputValue.trim();
    setInputValue("");

    const userMsg: MessageItem = {
      id: `user-${Date.now()}`,
      role: "user",
      content: userQuery,
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await authFetch(`${apiUrl}/api/books/${bookId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userQuery, top_k: 5 }),
      });

      if (!res.ok) throw new Error("Failed to get answer");

      const data = await res.json();
      const assistantMsg: MessageItem = {
        id: data.message_id || `asst-${Date.now()}`,
        role: "assistant",
        content: data.answer,
        sources: data.sources || [],
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: "Sorry, I encountered an issue retrieving information from this book.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const saveToNotes = async (msgId: string, content: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await authFetch(`${apiUrl}/api/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          book_id: bookId,
          title: `Chat Note - ${new Date().toLocaleDateString()}`,
          content: content,
          note_type: "ai_generated",
        }),
      });
      if (res.ok) {
        setSavedNotes((prev) => ({ ...prev, [msgId]: true }));
        if (onSavedToNotes) onSavedToNotes();
      }
    } catch (e) {
      console.error("Failed to save note:", e);
    }
  };

  return (
    <div className="flex h-[calc(100vh-8.5rem)] bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-xs">
      {/* Main Chat Thread */}
      <div className="flex-1 flex flex-col justify-between">
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3.5 max-w-2xl ${msg.role === "user" ? "ml-auto flex-row-reverse" : ""}`}
            >
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${
                  msg.role === "user"
                    ? "bg-indigo-600 text-white"
                    : "bg-gradient-to-tr from-violet-600 to-indigo-600 text-white"
                }`}
              >
                {msg.role === "user" ? <User className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
              </div>

              <div
                className={`p-4 rounded-2xl text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-indigo-600 text-white rounded-tr-xs"
                    : "bg-slate-50 border border-slate-200/80 text-slate-800 rounded-tl-xs"
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>

                {/* Sources & Save Actions for Assistant */}
                {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-slate-200/60">
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
                      Cited Sources
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {msg.sources.map((src, i) => (
                        <button
                          key={i}
                          onClick={() => src.page && onNavigateToPage(src.page)}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-xs text-indigo-700 font-semibold hover:border-indigo-300 hover:bg-indigo-50/50 transition-colors shadow-2xs"
                        >
                          <BookOpen className="h-3.5 w-3.5 text-indigo-500" />
                          Page {src.page || 1}
                        </button>
                      ))}
                    </div>

                    <div className="mt-3 flex justify-end">
                      <button
                        onClick={() => saveToNotes(msg.id, msg.content)}
                        disabled={savedNotes[msg.id]}
                        className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-indigo-600 font-medium py-1 px-2 rounded-md hover:bg-slate-100 transition-colors"
                      >
                        {savedNotes[msg.id] ? (
                          <>
                            <Check className="h-3.5 w-3.5 text-emerald-600" />
                            <span className="text-emerald-700">Saved to Notes</span>
                          </>
                        ) : (
                          <>
                            <BookmarkPlus className="h-3.5 w-3.5" />
                            Save to Notes
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-3.5 max-w-md">
              <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-violet-600 to-indigo-600 text-white flex items-center justify-center shrink-0">
                <Sparkles className="h-4 w-4" />
              </div>
              <div className="p-4 bg-slate-50 border border-slate-200/80 rounded-2xl rounded-tl-xs flex items-center gap-2 text-xs text-slate-500">
                <Loader2 className="h-4 w-4 animate-spin text-indigo-600" />
                Retrieving book chunks and formulating answer...
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-100 bg-white">
          <div className="relative flex items-center">
            <input
              type="text"
              placeholder="Ask anything about this book..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              className="w-full pl-4 pr-12 py-3 text-sm bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || loading}
              className="absolute right-2 p-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white rounded-lg transition-colors shadow-2xs"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
