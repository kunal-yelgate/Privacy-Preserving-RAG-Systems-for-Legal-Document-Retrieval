"use client";

import React, { useEffect } from "react";
import { AlertTriangle, RefreshCw, Home, Terminal } from "lucide-react";
import Link from "next/link";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Caught runtime boundary error:", error);
  }, [error]);

  const isFetchError =
    error?.message?.toLowerCase().includes("fetch") ||
    error?.message?.toLowerCase().includes("network") ||
    error?.message?.toLowerCase().includes("unable to reach");

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 rounded-2xl p-8 max-w-xl w-full shadow-lg space-y-6 text-center">
        <div className="w-14 h-14 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto border border-rose-100">
          <AlertTriangle className="w-8 h-8" />
        </div>

        <div className="space-y-2">
          <h2 className="text-xl font-bold tracking-tight text-slate-900">
            {isFetchError ? "Backend Connection Offline" : "Something went wrong"}
          </h2>
          <p className="text-xs text-slate-500 leading-relaxed max-w-md mx-auto">
            {isFetchError
              ? "The frontend was unable to connect to the local FastAPI backend (127.0.0.1:8000). Please start the backend service."
              : error.message || "An unexpected error occurred while rendering this page."}
          </p>
        </div>

        {isFetchError && (
          <div className="bg-slate-900 text-left p-3.5 rounded-xl space-y-1.5 font-mono text-xs text-slate-300">
            <p className="text-[11px] text-slate-400 flex items-center gap-1">
              <Terminal className="w-3.5 h-3.5 text-emerald-400" />
              <span>Start the local backend from project root:</span>
            </p>
            <p className="text-emerald-400 text-[11px] select-all">
              .\venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
            </p>
          </div>
        )}

        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            onClick={() => reset()}
            className="flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Try Again</span>
          </button>
          <Link
            href="/"
            className="flex items-center gap-1.5 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
          >
            <Home className="w-3.5 h-3.5" />
            <span>Go to Dashboard</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
