"use client";

import React, { useState } from "react";
import { FileText, Sparkles, Loader2, CheckCircle2, BookmarkPlus } from "lucide-react";
import { authFetch } from "@/lib/auth";

interface SummaryPanelProps {
  bookId: string;
}

export default function SummaryPanel({ bookId }: SummaryPanelProps) {
  const [summaryType, setSummaryType] = useState("detailed");
  const [summaryData, setSummaryData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const generateSummary = async (type: string) => {
    setSummaryType(type);
    setLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await authFetch(`${apiUrl}/api/books/${bookId}/summary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ summary_type: type }),
      });
      if (res.ok) {
        const data = await res.json();
        setSummaryData(data);
      }
    } catch (e) {
      console.error("Summary failed:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-8.5rem)] bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-xs">
      {/* Types Sidebar */}
      <div className="w-64 border-r border-slate-200 bg-slate-50/50 p-4 space-y-2">
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
          Summary Types
        </h4>

        {[
          { id: "quick", label: "Quick Summary", desc: "Key thesis in 2 minutes" },
          { id: "detailed", label: "Detailed Summary", desc: "Comprehensive breakdown" },
          { id: "key_ideas", label: "Key Ideas & Arguments", desc: "Core conceptual takeaways" },
          { id: "study_guide", label: "Study Guide", desc: "Review questions & frameworks" },
        ].map((item) => (
          <button
            key={item.id}
            onClick={() => generateSummary(item.id)}
            className={`w-full text-left p-3 rounded-xl transition-all ${
              summaryType === item.id
                ? "bg-white border border-indigo-200 shadow-xs text-indigo-900"
                : "text-slate-600 hover:bg-slate-100/80"
            }`}
          >
            <div className="font-semibold text-xs text-slate-900">{item.label}</div>
            <div className="text-[11px] text-slate-500 mt-0.5">{item.desc}</div>
          </button>
        ))}
      </div>

      {/* Content View */}
      <div className="flex-1 overflow-y-auto p-8 lg:px-16">
        {loading ? (
          <div className="text-center py-24 space-y-3">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-600 mx-auto" />
            <p className="text-sm text-slate-600 font-medium">
              Synthesizing hierarchical summary from book chapters...
            </p>
          </div>
        ) : summaryData ? (
          <div className="max-w-3xl space-y-8">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full">
                {summaryData.summary_type.replace("_", " ")}
              </span>
              <h2 className="text-2xl font-bold text-slate-900 mt-3">{summaryData.title}</h2>
            </div>

            <div className="text-slate-700 leading-relaxed text-sm sm:text-base font-serif whitespace-pre-wrap bg-slate-50/50 p-6 rounded-2xl border border-slate-100">
              {summaryData.summary}
            </div>

            {summaryData.key_takeaways && summaryData.key_takeaways.length > 0 && (
              <div>
                <h3 className="text-base font-bold text-slate-900 mb-4">Core Takeaways</h3>
                <div className="space-y-2">
                  {summaryData.key_takeaways.map((point: string, idx: number) => (
                    <div key={idx} className="flex items-start gap-3 p-3 bg-white border border-slate-200 rounded-xl">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                      <span className="text-xs text-slate-700 font-medium">{point}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-24">
            <FileText className="h-12 w-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-slate-800">Generate a Summary</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto mb-6">
              Select a summary format from the left panel to synthesize chapters into clear, actionable insights.
            </p>
            <button
              onClick={() => generateSummary("detailed")}
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-xs font-semibold rounded-xl shadow-sm hover:bg-indigo-700"
            >
              <Sparkles className="h-4 w-4" />
              Generate Detailed Summary
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
