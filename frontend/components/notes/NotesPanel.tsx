"use client";

import React, { useState, useEffect } from "react";
import { Plus, Sparkles, Trash2, Edit3, Check, Loader2, BookOpen } from "lucide-react";
import { authFetch } from "@/lib/auth";

interface Note {
  id: string;
  book_id?: string;
  title: string;
  content: string;
  note_type: string;
  updated_at: string;
}

interface NotesPanelProps {
  bookId: string;
}

export default function NotesPanel({ bookId }: NotesPanelProps) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [editingContent, setEditingContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const fetchNotes = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await authFetch(`${apiUrl}/api/notes?book_id=${bookId}`);
      if (res.ok) {
        const data = await res.json();
        setNotes(data);
        if (data.length > 0 && !selectedNote) {
          setSelectedNote(data[0]);
          setEditingTitle(data[0].title);
          setEditingContent(data[0].content);
        }
      }
    } catch (e) {
      console.error("Failed to load notes:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotes();
  }, [bookId]);

  const handleSelectNote = (note: Note) => {
    setSelectedNote(note);
    setEditingTitle(note.title);
    setEditingContent(note.content);
  };

  const handleSaveCurrentNote = async () => {
    if (!selectedNote) return;
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await authFetch(`${apiUrl}/api/notes/${selectedNote.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: editingTitle,
          content: editingContent,
        }),
      });
      if (res.ok) {
        fetchNotes();
      }
    } catch (e) {
      console.error("Save note failed:", e);
    }
  };

  const handleCreateEmptyNote = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await authFetch(`${apiUrl}/api/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          book_id: bookId,
          title: "Untitled Note",
          content: "Write your structured notes or thoughts here...",
          note_type: "manual",
        }),
      });
      if (res.ok) {
        const newNote = await res.json();
        setNotes((prev) => [newNote, ...prev]);
        handleSelectNote(newNote);
      }
    } catch (e) {
      console.error("Create note failed:", e);
    }
  };

  const handleGenerateAINote = async (noteType: string) => {
    setGenerating(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await authFetch(`${apiUrl}/api/notes/generate?book_id=${bookId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ note_type: noteType }),
      });
      if (res.ok) {
        const structured = await res.json();
        let formatted = `${structured.summary || ""}\n\n`;
        if (structured.sections) {
          structured.sections.forEach((sec: any) => {
            formatted += `### ${sec.heading}\n`;
            sec.points.forEach((pt: string) => {
              formatted += `• ${pt}\n`;
            });
            formatted += `\n`;
          });
        }

        // Save as note
        const saveRes = await authFetch(`${apiUrl}/api/notes`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            book_id: bookId,
            title: structured.title || `AI ${noteType.replace("_", " ").toUpperCase()}`,
            content: formatted,
            note_type: "ai_generated",
          }),
        });
        if (saveRes.ok) {
          const created = await saveRes.json();
          setNotes((prev) => [created, ...prev]);
          handleSelectNote(created);
        }
      }
    } catch (e) {
      console.error("AI Note generation failed:", e);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-8.5rem)] bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-xs">
      {/* Notes List Sidebar */}
      <div className="w-80 border-r border-slate-200 bg-slate-50/50 p-4 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-800 text-sm">Notes & Study Guides</h3>
            <button
              onClick={handleCreateEmptyNote}
              className="p-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 hover:text-indigo-600 hover:border-indigo-200 transition-colors shadow-2xs"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>

          {/* AI Generator dropdown / buttons */}
          <div className="mb-4 p-3 bg-indigo-50/60 border border-indigo-100 rounded-xl space-y-2">
            <div className="text-[11px] font-bold text-indigo-800 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
              AI Note Assistant
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleGenerateAINote("study_notes")}
                disabled={generating}
                className="flex-1 py-1.5 px-2 bg-white text-indigo-700 text-xs font-semibold rounded-lg border border-indigo-200 hover:bg-indigo-50 transition-colors"
              >
                {generating ? "Generating..." : "Study Notes"}
              </button>
              <button
                onClick={() => handleGenerateAINote("key_points")}
                disabled={generating}
                className="flex-1 py-1.5 px-2 bg-white text-indigo-700 text-xs font-semibold rounded-lg border border-indigo-200 hover:bg-indigo-50 transition-colors"
              >
                Key Points
              </button>
            </div>
          </div>

          <div className="space-y-1 overflow-y-auto max-h-[calc(100vh-22rem)]">
            {notes.map((note) => (
              <button
                key={note.id}
                onClick={() => handleSelectNote(note)}
                className={`w-full text-left p-3 rounded-xl transition-all ${
                  selectedNote?.id === note.id
                    ? "bg-white border border-indigo-200 shadow-xs text-indigo-950"
                    : "text-slate-700 hover:bg-slate-100/80"
                }`}
              >
                <p className="font-semibold text-xs truncate">{note.title}</p>
                <p className="text-[11px] text-slate-400 mt-1 truncate">
                  {note.content.slice(0, 60)}...
                </p>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Note Editor Area */}
      <div className="flex-1 flex flex-col bg-white">
        {selectedNote ? (
          <div className="flex-1 flex flex-col p-8 lg:px-14">
            <div className="flex items-center justify-between pb-4 mb-6 border-b border-slate-100">
              <input
                type="text"
                value={editingTitle}
                onChange={(e) => setEditingTitle(e.target.value)}
                onBlur={handleSaveCurrentNote}
                className="text-2xl font-bold text-slate-900 border-none outline-hidden w-full focus:ring-0"
              />
              <button
                onClick={handleSaveCurrentNote}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-semibold transition-colors"
              >
                <Check className="h-3.5 w-3.5" />
                Save Note
              </button>
            </div>

            <textarea
              value={editingContent}
              onChange={(e) => setEditingContent(e.target.value)}
              onBlur={handleSaveCurrentNote}
              rows={20}
              className="flex-1 w-full text-sm sm:text-base leading-relaxed text-slate-800 border-none outline-hidden resize-none font-serif focus:ring-0"
              placeholder="Write or edit notes here..."
            />
          </div>
        ) : (
          <div className="text-center py-32 text-slate-400 text-sm">
            Select or create a note to view and edit.
          </div>
        )}
      </div>
    </div>
  );
}
