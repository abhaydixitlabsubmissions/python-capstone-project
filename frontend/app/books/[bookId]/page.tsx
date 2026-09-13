"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  BookOpen,
  ArrowLeft,
  MessageSquare,
  FileText,
  Bookmark,
  Share2,
  CheckCircle,
  ExternalLink,
  Layers,
} from "lucide-react";
import ReaderPanel from "@/components/reader/ReaderPanel";
import ChatPanel from "@/components/chat/ChatPanel";
import SummaryPanel from "@/components/summary/SummaryPanel";
import NotesPanel from "@/components/notes/NotesPanel";
import { authFetch } from "@/lib/auth";

interface Book {
  id: string;
  title: string;
  author?: string;
  file_type: string;
  page_count: number;
  word_count: number;
  status: string;
}

interface SimilarBook {
  book_id: string;
  title: string;
  author?: string;
  similarity_score: number;
  relationship_type: string;
}

export default function BookDetailPage() {
  const params = useParams();
  const bookId = params.bookId as string;
  const router = useRouter();

  const [book, setBook] = useState<Book | null>(null);
  const [activeTab, setActiveTab] = useState<"read" | "chat" | "summary" | "notes" | "related">("read");
  const [targetPage, setTargetPage] = useState<number | null>(null);
  const [relatedBooks, setRelatedBooks] = useState<SimilarBook[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchBookDetails = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await authFetch(`${apiUrl}/api/books/${bookId}`);
        if (res.ok) {
          const data = await res.json();
          setBook(data);
        }

        // Fetch related documents in library
        const relRes = await authFetch(`${apiUrl}/api/books/${bookId}/related`);
        if (relRes.ok) {
          const relData = await relRes.json();
          setRelatedBooks(relData);
        }
      } catch (e) {
        console.error("Failed to load book:", e);
      } finally {
        setLoading(false);
      }
    };

    if (bookId) fetchBookDetails();
  }, [bookId]);

  const handleNavigateToPage = (page: number) => {
    setTargetPage(page);
    setActiveTab("read");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center text-sm text-slate-500">
        Loading book workspace...
      </div>
    );
  }

  if (!book) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
        <h2 className="text-lg font-bold text-slate-800">Book Not Found</h2>
        <Link href="/dashboard" className="text-sm text-indigo-600 hover:underline mt-2">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top App Header */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/dashboard"
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
            </Link>

            <div>
              <h1 className="font-bold text-slate-900 text-sm sm:text-base line-clamp-1">
                {book.title}
              </h1>
              <p className="text-xs text-slate-400">
                {book.author || "Unknown Author"} • {book.page_count} pages
              </p>
            </div>
          </div>

          {/* Navigation Tabs (Read | Chat | Summary | Notes | Related) */}
          <div className="flex items-center bg-slate-100/80 p-1 rounded-xl border border-slate-200/60">
            {[
              { id: "read", label: "Read", icon: BookOpen },
              { id: "chat", label: "Chat", icon: MessageSquare },
              { id: "summary", label: "Summary", icon: FileText },
              { id: "notes", label: "Notes", icon: Bookmark },
              { id: "related", label: "Related", icon: Layers },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activeTab === tab.id
                      ? "bg-white text-indigo-600 shadow-2xs font-bold"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </header>

      {/* Main Tab Workspace */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 w-full">
        {activeTab === "read" && (
          <ReaderPanel bookId={book.id} targetPage={targetPage} />
        )}

        {activeTab === "chat" && (
          <ChatPanel
            bookId={book.id}
            onNavigateToPage={handleNavigateToPage}
          />
        )}

        {activeTab === "summary" && (
          <SummaryPanel bookId={book.id} />
        )}

        {activeTab === "notes" && (
          <NotesPanel bookId={book.id} />
        )}

        {activeTab === "related" && (
          <div className="bg-white rounded-2xl border border-slate-200 p-8 max-w-4xl mx-auto">
            <div className="mb-6">
              <h2 className="text-lg font-bold text-slate-900">Similar Documents in Your Library</h2>
              <p className="text-xs text-slate-500 mt-1">
                Conceptually and semantically linked documents discovered through pgvector similarity scoring.
              </p>
            </div>

            {relatedBooks.length === 0 ? (
              <div className="text-center py-16 text-slate-400 text-xs">
                No related documents found in your library yet. As you upload more books, BookMind will automatically discover cross-book connections!
              </div>
            ) : (
              <div className="space-y-3">
                {relatedBooks.map((item) => (
                  <div
                    key={item.book_id}
                    className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/50 hover:bg-white hover:border-indigo-200 transition-all flex items-center justify-between"
                  >
                    <div>
                      <h4 className="font-semibold text-sm text-slate-800">{item.title}</h4>
                      <p className="text-xs text-slate-400">{item.author || "Unknown Author"}</p>
                      <span className="inline-block mt-1 text-[11px] font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-200/60">
                        {Math.round(item.similarity_score * 100)}% match • {item.relationship_type.replace("_", " ")}
                      </span>
                    </div>

                    <Link
                      href={`/books/${item.book_id}`}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 px-3 py-1.5 rounded-lg border border-indigo-200 bg-white"
                    >
                      View Book
                      <ExternalLink className="h-3.5 w-3.5" />
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
