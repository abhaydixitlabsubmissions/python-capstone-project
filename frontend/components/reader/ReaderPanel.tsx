"use client";

import React, { useState, useEffect } from "react";
import { BookOpen, Search, ArrowLeft, ArrowRight, Bookmark } from "lucide-react";
import { authFetch } from "@/lib/auth";

interface Chunk {
  id: string;
  chunk_index: number;
  content: string;
  page_start?: number;
  page_end?: number;
  chapter?: string;
  section?: string;
}

interface ReaderPanelProps {
  bookId: string;
  targetPage?: number | null;
}

export default function ReaderPanel({ bookId, targetPage }: ReaderPanelProps) {
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [loading, setLoading] = useState(true);
  const [activePage, setActivePage] = useState<number>(1);
  const [filterQuery, setFilterQuery] = useState("");

  useEffect(() => {
    const fetchChunks = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await authFetch(`${apiUrl}/api/books/${bookId}/chunks?limit=100`);
        if (res.ok) {
          const data = await res.json();
          setChunks(data);
        }
      } catch (e) {
        console.error("Failed to load chunks:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchChunks();
  }, [bookId]);

  useEffect(() => {
    if (targetPage) {
      setActivePage(targetPage);
      const element = document.getElementById(`page-${targetPage}`);
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  }, [targetPage]);

  const filteredChunks = chunks.filter((c) =>
    filterQuery ? c.content.toLowerCase().includes(filterQuery.toLowerCase()) : true
  );

  return (
    <div className="flex h-[calc(100vh-8.5rem)] bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-xs">
      {/* Reader Sidebar: Outline / Navigation */}
      <div className="w-72 border-r border-slate-200 bg-slate-50/50 p-4 flex flex-col">
        <div className="relative mb-3">
          <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Filter text in book..."
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg outline-hidden focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
          Document Outline
        </h4>

        <div className="flex-1 overflow-y-auto space-y-1 pr-1">
          {chunks.map((c) => (
            <button
              key={c.id}
              onClick={() => {
                if (c.page_start) {
                  setActivePage(c.page_start);
                  document.getElementById(`page-${c.page_start}`)?.scrollIntoView({ behavior: "smooth" });
                }
              }}
              className={`w-full text-left px-2.5 py-2 rounded-lg text-xs transition-colors flex items-center justify-between ${
                activePage === c.page_start
                  ? "bg-indigo-50 text-indigo-700 font-semibold border border-indigo-200/60"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <span className="truncate max-w-[170px]">
                {c.chapter || `Section (Chunk #${c.chunk_index + 1})`}
              </span>
              <span className="text-[10px] text-slate-400 font-mono">
                p.{c.page_start || 1}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Reader Main Text Container */}
      <div className="flex-1 overflow-y-auto p-8 lg:px-16 bg-white space-y-8">
        {loading ? (
          <div className="text-center py-20 text-slate-400 text-sm">Loading document text...</div>
        ) : filteredChunks.length === 0 ? (
          <div className="text-center py-20 text-slate-400 text-sm">No text matching search.</div>
        ) : (
          filteredChunks.map((chunk) => (
            <article
              key={chunk.id}
              id={`page-${chunk.page_start}`}
              className={`pb-8 border-b border-slate-100 transition-all ${
                activePage === chunk.page_start ? "bg-indigo-50/20 -mx-4 px-4 py-4 rounded-xl" : ""
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-indigo-600 bg-indigo-50 px-2.5 py-0.5 rounded-full">
                  Page {chunk.page_start || 1}
                </span>
                {chunk.chapter && (
                  <span className="text-xs font-semibold text-slate-500">
                    {chunk.chapter}
                  </span>
                )}
              </div>

              <div className="text-slate-800 text-sm sm:text-base leading-relaxed whitespace-pre-wrap font-serif">
                {chunk.content}
              </div>
            </article>
          ))
        )}
      </div>
    </div>
  );
}
