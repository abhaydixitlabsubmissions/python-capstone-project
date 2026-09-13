"use client";

import React, { useState, useRef } from "react";
import { UploadCloud, X, AlertTriangle, CheckCircle2, FileText, ArrowRight, Loader2 } from "lucide-react";
import { authFetch } from "@/lib/auth";

interface SimilarDocument {
  book_id: string;
  title: string;
  author?: string;
  similarity_score: number;
  relationship_type: string;
}

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (bookId: string) => void;
}

export default function UploadModal({ isOpen, onClose, onSuccess }: UploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [uploading, setUploading] = useState(false);
  const [step, setStep] = useState<"select" | "similarity_warning" | "processing">("select");
  const [similarDocs, setSimilarDocs] = useState<SimilarDocument[]>([]);
  const [isExactDuplicate, setIsExactDuplicate] = useState(false);
  const [createdBookId, setCreatedBookId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      if (!title) {
        setTitle(selectedFile.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " "));
      }
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", title || file.name);
    if (author) formData.append("author", author);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await authFetch(`${apiUrl}/api/books`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Upload failed.");
      }

      const data = await res.json();
      setCreatedBookId(data.book.id);

      const simCheck = data.similarity_check;
      if (simCheck.is_exact_duplicate || (simCheck.similar_documents && simCheck.similar_documents.length > 0)) {
        setIsExactDuplicate(simCheck.is_exact_duplicate);
        setSimilarDocs(simCheck.similar_documents || []);
        setStep("similarity_warning");
        setUploading(false);
      } else {
        // Proceed straight to background ingestion
        triggerProcessing(data.book.id);
      }
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
      setUploading(false);
    }
  };

  const triggerProcessing = async (bookId: string) => {
    setStep("processing");
    setUploading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await authFetch(`${apiUrl}/api/books/${bookId}/process`, {
        method: "POST",
      });
      if (!res.ok) throw new Error("Processing failed.");
      onSuccess(bookId);
    } catch (err: any) {
      setError(err.message || "Ingestion failed.");
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-100 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-800">
            {step === "similarity_warning" ? "Similar Documents Found" : "Upload Book to Library"}
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 font-medium">
              {error}
            </div>
          )}

          {step === "select" && (
            <div className="space-y-4">
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-200 hover:border-indigo-400 bg-slate-50/50 hover:bg-indigo-50/20 rounded-xl p-8 text-center cursor-pointer transition-all"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.epub"
                  className="hidden"
                  onChange={handleFileChange}
                />
                <div className="h-12 w-12 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center mx-auto mb-3">
                  <UploadCloud className="h-6 w-6" />
                </div>
                {file ? (
                  <div className="text-sm font-semibold text-slate-800 flex items-center justify-center gap-2">
                    <FileText className="h-4 w-4 text-indigo-600" />
                    {file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                  </div>
                ) : (
                  <>
                    <p className="text-sm font-semibold text-slate-700">Drag & drop your file or choose file</p>
                    <p className="text-xs text-slate-400 mt-1">Supports PDF • EPUB • DOCX (up to 100MB)</p>
                  </>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Book Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Atomic Habits"
                  className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Author (Optional)</label>
                <input
                  type="text"
                  value={author}
                  onChange={(e) => setAuthor(e.target.value)}
                  placeholder="e.g. James Clear"
                  className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg font-medium"
                >
                  Cancel
                </button>
                <button
                  disabled={!file || uploading}
                  onClick={handleUpload}
                  className="px-5 py-2 text-sm text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-lg font-medium shadow-sm flex items-center gap-2"
                >
                  {uploading && <Loader2 className="h-4 w-4 animate-spin" />}
                  Check & Upload
                </button>
              </div>
            </div>
          )}

          {step === "similarity_warning" && (
            <div className="space-y-4">
              <div className="flex items-start gap-3 p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-amber-900">
                <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
                <div className="text-xs">
                  <p className="font-semibold">
                    {isExactDuplicate ? "Exact Duplicate Detected" : "Similar Documents Found in Library"}
                  </p>
                  <p className="text-amber-700 mt-0.5">
                    We detected existing books in your library matching this file. You can open an existing book or proceed with processing.
                  </p>
                </div>
              </div>

              <div className="space-y-2 max-h-56 overflow-y-auto">
                {similarDocs.map((doc) => (
                  <div
                    key={doc.book_id}
                    className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between"
                  >
                    <div>
                      <p className="text-sm font-semibold text-slate-800">{doc.title}</p>
                      <p className="text-xs text-slate-500">{doc.author || "Unknown Author"}</p>
                      <span className="inline-block mt-1 text-[11px] font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-200/50">
                        {Math.round(doc.similarity_score * 100)}% match • {doc.relationship_type.replace("_", " ")}
                      </span>
                    </div>

                    <button
                      onClick={() => onSuccess(doc.book_id)}
                      className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 px-3 py-1.5 rounded-lg border border-indigo-200 flex items-center gap-1"
                    >
                      Open
                      <ArrowRight className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>

              <div className="flex justify-between items-center pt-2">
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={() => createdBookId && triggerProcessing(createdBookId)}
                  className="px-5 py-2 text-sm text-white bg-slate-800 hover:bg-slate-900 rounded-lg font-medium shadow-sm"
                >
                  Upload Anyway
                </button>
              </div>
            </div>
          )}

          {step === "processing" && (
            <div className="text-center py-8 space-y-4">
              <Loader2 className="h-10 w-10 text-indigo-600 animate-spin mx-auto" />
              <div>
                <h3 className="text-base font-bold text-slate-800">Processing Book Content</h3>
                <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
                  Extracting text, detecting chapters, creating chunks, and computing vector embeddings...
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
