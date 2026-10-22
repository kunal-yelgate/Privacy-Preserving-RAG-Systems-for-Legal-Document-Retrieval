"use client";
import React from "react";
import { AlertCircle, WifiOff, RefreshCw, Terminal, ChevronRight } from "lucide-react";

interface BackendErrorBannerProps {
  title?: string;
  message?: string;
  isConnectionError?: boolean;
  onRetry?: () => void;
  retrying?: boolean;
  className?: string;
}

export function BackendErrorBanner({
  title,
  message,
  isConnectionError = true,
  onRetry,
  retrying = false,
  className = "",
}: BackendErrorBannerProps) {
  const displayTitle = title || (isConnectionError ? "Local Backend Connection Failed" : "API Operation Failed");
  const displayMessage =
    message ||
    (isConnectionError
      ? "The frontend cannot connect to the local FastAPI backend at 127.0.0.1:8000. Features requiring retrieval, ingestion, or inference are currently unavailable."
      : "An unexpected error occurred while communicating with the backend service.");

  return (
    <div
      role="alert"
      className={`bg-rose-50/90 border border-rose-200 rounded-xl p-4 sm:p-5 text-rose-900 shadow-sm space-y-3 ${className}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-rose-100 rounded-lg text-rose-700 flex-shrink-0 mt-0.5">
            {isConnectionError ? <WifiOff className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
          </div>
          <div className="space-y-1">
            <h3 className="font-bold text-sm text-rose-900 leading-tight">{displayTitle}</h3>
            <p className="text-xs text-rose-800 leading-relaxed max-w-3xl">{displayMessage}</p>
          </div>
        </div>

        {onRetry && (
          <button
            onClick={onRetry}
            disabled={retrying}
            className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 bg-rose-900 hover:bg-rose-800 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${retrying ? "animate-spin" : ""}`} />
            <span>{retrying ? "Retrying..." : "Retry"}</span>
          </button>
        )}
      </div>

      {isConnectionError && (
        <div className="pt-2 border-t border-rose-200/60 text-xs space-y-1.5 text-rose-900">
          <p className="font-semibold flex items-center gap-1 text-[11px] uppercase tracking-wider text-rose-800">
            <Terminal className="w-3.5 h-3.5" />
            <span>How to launch the backend (PowerShell in project root):</span>
          </p>
          <div className="bg-slate-900 text-emerald-400 p-2.5 rounded-lg font-mono text-[11px] overflow-x-auto flex items-center justify-between">
            <code>.\venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload</code>
          </div>
        </div>
      )}
    </div>
  );
}
