"use client";

import React, { useEffect, useState, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Search,
  Send,
  BookOpen,
  FileText,
  AlertCircle,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Cpu,
  HelpCircle,
  ExternalLink,
  RefreshCw,
} from "lucide-react";
import { api, getErrorMessage, isApiError } from "@/lib/api/client";
import { CitationReference, Matter } from "@/types";
import { BackendErrorBanner } from "@/components/ui/BackendErrorBanner";
import { useAuth } from "@/contexts/AuthContext";

interface MessageItem {
  id: string;
  sender: "user" | "assistant";
  content: string;
  citations?: CitationReference[];
  timestamp: string;
}

function ResearchContent() {
  const searchParams = useSearchParams();
  const matterParam = searchParams.get("matter");
  const { authReady, backendOnline } = useAuth();

  const [matters, setMatters] = useState<Matter[]>([]);
  const [selectedMatter, setSelectedMatter] = useState<string>(matterParam || "");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [activeCitation, setActiveCitation] = useState<CitationReference | null>(null);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [initError, setInitError] = useState<string | null>(null);
  const [isConnError, setIsConnError] = useState(false);
  const [loadingMatters, setLoadingMatters] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const initMatters = async () => {
    setLoadingMatters(true);
    setInitError(null);
    try {
      const m = await api.listMatters();
      setMatters(m);
      if (m.length > 0 && !selectedMatter) {
        setSelectedMatter(m[0].matter_id);
      }
    } catch (err: any) {
      console.error("Failed to load matters in research:", err);
      setInitError(getErrorMessage(err));
      setIsConnError(isApiError(err) ? err.isConnectionError : true);
    } finally {
      setLoadingMatters(false);
    }
  };

  useEffect(() => {
    if (!authReady) return;
    if (!backendOnline) {
      setInitError("Backend is offline. Ensure the FastAPI server is running on 127.0.0.1:8000.");
      setIsConnError(true);
      setLoadingMatters(false);
      return;
    }
    initMatters();
  }, [authReady, backendOnline]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, submitting]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || !selectedMatter || submitting) return;

    const userQ = question.trim();
    setQuestion("");
    setErrorMsg(null);

    const userMessage: MessageItem = {
      id: `usr_${Date.now()}`,
      sender: "user",
      content: userQ,
      timestamp: new Date().toLocaleTimeString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setSubmitting(true);

    try {
      const res = await api.askQuestion(userQ, selectedMatter, sessionId);
      setSessionId(res.session_id);

      const assistantMessage: MessageItem = {
        id: `asst_${Date.now()}`,
        sender: "assistant",
        content: res.answer,
        citations: res.citations,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      setErrorMsg(getErrorMessage(err, "Inference failed. Check local backend and Ollama readiness."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Research Workspace</h1>
          <p className="text-sm text-slate-500 mt-1">
            Evidence-grounded, citation-verified legal intelligence powered by local offline inference.
          </p>
        </div>

        {/* Matter Selector Boundary */}
        <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-slate-600">Active Boundary:</span>
          <select
            value={selectedMatter}
            onChange={(e) => {
              setSelectedMatter(e.target.value);
              setMessages([]);
              setSessionId(undefined);
            }}
            className="text-xs font-bold text-slate-900 bg-transparent focus:outline-none cursor-pointer"
          >
            {matters.length === 0 && <option value="">No matters available</option>}
            {matters.map((m) => (
              <option key={m.matter_id} value={m.matter_id}>
                {m.name} ({m.matter_id})
              </option>
            ))}
          </select>
          <button
            onClick={initMatters}
            className="p-1 rounded hover:bg-slate-100 text-slate-500 transition-colors ml-1"
            title="Refresh Matters"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingMatters ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Backend Connection Error Banner */}
      {initError && (
        <BackendErrorBanner
          message={initError}
          isConnectionError={isConnError}
          onRetry={initMatters}
          retrying={loadingMatters}
        />
      )}

      {/* Main Research Container */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat / Question Section */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col h-[650px]">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-3">
                <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
                  <BookOpen className="w-6 h-6" />
                </div>
                <div className="space-y-1">
                  <h3 className="font-bold text-slate-800 text-sm">No Active Research Queries</h3>
                  <p className="text-xs text-slate-500 max-w-sm">
                    Enter a question regarding the active matter. Only authorized documents inside{" "}
                    <span className="font-mono font-semibold text-slate-700">{selectedMatter}</span>{" "}
                    will be retrieved and used for generation.
                  </p>
                </div>

                {/* Example Prompts */}
                <div className="pt-4 flex flex-wrap gap-2 justify-center max-w-md">
                  <button
                    onClick={() => setQuestion("What is the total acquisition consideration and governing law?")}
                    className="text-[11px] bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 px-2.5 py-1.5 rounded-md transition-colors"
                  >
                    💡 What is the purchase consideration?
                  </button>
                  <button
                    onClick={() => setQuestion("What are the post-termination covenants and severance terms?")}
                    className="text-[11px] bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 px-2.5 py-1.5 rounded-md transition-colors"
                  >
                    💡 Non-compete and severance terms?
                  </button>
                </div>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
                >
                  <div
                    className={`max-w-[85%] rounded-xl p-4 text-xs space-y-2 leading-relaxed ${
                      msg.sender === "user"
                        ? "bg-slate-900 text-white"
                        : "bg-slate-50 border border-slate-200 text-slate-800"
                    }`}
                  >
                    <div className="flex items-center justify-between text-[10px] opacity-70 mb-1">
                      <span className="font-semibold uppercase tracking-wider">
                        {msg.sender === "user" ? "Researcher" : "Veritas Assistant"}
                      </span>
                      <span>{msg.timestamp}</span>
                    </div>

                    <div className="whitespace-pre-wrap font-sans text-xs">{msg.content}</div>

                    {/* Citations Footer for Assistant */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="pt-3 border-t border-slate-200/60 mt-3 space-y-1.5">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1">
                          <FileText className="w-3 h-3 text-slate-400" />
                          <span>Verified Documentary Sources:</span>
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.citations.map((cite) => (
                            <button
                              key={cite.citation_id}
                              onClick={() => setActiveCitation(cite)}
                              className="text-[11px] font-semibold bg-white hover:bg-blue-50 border border-slate-200 hover:border-blue-300 text-blue-700 px-2 py-0.5 rounded shadow-2xs transition-all flex items-center gap-1"
                            >
                              <span>[{cite.citation_id}]</span>
                              <span className="max-w-[130px] truncate">{cite.document_title}</span>
                              <span className="text-slate-400">p.{cite.page_number}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}

            {submitting && (
              <div className="flex items-center gap-2 text-xs text-slate-500 py-2">
                <span className="w-2 h-2 rounded-full bg-blue-600 animate-ping"></span>
                <span>Searching ChromaDB & generating grounded response via local Ollama...</span>
              </div>
            )}

            {errorMsg && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-600" />
                <span>{errorMsg}</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Box */}
          <form onSubmit={handleSubmit} className="p-3 border-t border-slate-200 bg-slate-50 flex gap-2">
            <input
              type="text"
              placeholder={`Ask a question within matter '${selectedMatter}'...`}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={submitting}
              className="flex-1 text-xs border border-slate-200 rounded-lg px-3 py-2.5 bg-white focus:outline-none focus:ring-1 focus:ring-slate-900"
            />
            <button
              type="submit"
              disabled={submitting || !question.trim()}
              className="px-4 py-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Ask</span>
            </button>
          </form>
        </div>

        {/* Supporting Evidence / Citations Inspector Panel */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col justify-between h-[650px] overflow-hidden">
          <div className="space-y-4 flex-1 overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <FileText className="w-4 h-4 text-slate-600" />
                <span>Evidence Inspector</span>
              </h2>
              <span className="text-[10px] uppercase font-semibold text-slate-400">Provenance</span>
            </div>

            {activeCitation ? (
              <div className="space-y-3 animate-fadeIn">
                <div className="bg-blue-50/70 border border-blue-200 p-3 rounded-lg space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-blue-900 font-mono">[{activeCitation.citation_id}]</span>
                    <span className="text-[11px] font-semibold text-blue-700 bg-blue-100 px-2 py-0.5 rounded">
                      Page {activeCitation.page_number}
                    </span>
                  </div>
                  <h3 className="font-semibold text-slate-900 text-xs">{activeCitation.document_title}</h3>
                  <p className="text-[10px] text-slate-500 font-mono">Doc ID: {activeCitation.document_id}</p>
                </div>

                <div className="space-y-1.5">
                  <label className="text-[11px] font-bold uppercase text-slate-400 tracking-wider">
                    Authorized Passage Snippet:
                  </label>
                  <div className="bg-slate-50 border border-slate-200 p-3 rounded-lg text-xs text-slate-700 leading-relaxed font-serif whitespace-pre-wrap max-h-72 overflow-y-auto">
                    {activeCitation.snippet}
                  </div>
                </div>

                <div className="bg-emerald-50 border border-emerald-200 p-2.5 rounded-lg text-[11px] text-emerald-800 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  <span>Verified: Retrieved chunk matches matter authorization filter.</span>
                </div>
              </div>
            ) : (
              <div className="h-64 flex flex-col items-center justify-center text-center p-4 space-y-2 text-slate-400">
                <BookOpen className="w-8 h-8 text-slate-300" />
                <p className="text-xs font-medium text-slate-500">No Citation Selected</p>
                <p className="text-[11px]">
                  Click any <span className="font-mono text-blue-600">[cite-X]</span> button in an answer
                  to inspect the supporting passage and page number.
                </p>
              </div>
            )}
          </div>

          {/* Legal Disclaimer Pill */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-[10px] text-slate-500 leading-tight">
            ⚠️ <strong>Legal Disclaimer:</strong> Generated responses are grounded exclusively in retrieved local
            documents and do not constitute formal legal counsel. Always review original source citations.
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ResearchWorkspacePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-slate-400">Loading research workspace...</div>}>
      <ResearchContent />
    </Suspense>
  );
}
