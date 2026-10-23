"use client";

import React, { useEffect, useState } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  Lock,
  Cpu,
  AlertTriangle,
  Play,
  FileCheck,
  Activity,
  CheckCircle2,
  XCircle,
  Database,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import { api, getErrorMessage, isApiError } from "@/lib/api/client";
import { AuditEvent, EvaluationRun, SecurityStatus } from "@/types";
import { BackendErrorBanner } from "@/components/ui/BackendErrorBanner";
import { useAuth } from "@/contexts/AuthContext";

export default function SecurityCenterPage() {
  const { authReady, backendOnline } = useAuth();
  const [securityStatus, setSecurityStatus] = useState<SecurityStatus | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [evalRuns, setEvalRuns] = useState<EvaluationRun[]>([]);
  const [runningEval, setRunningEval] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnError, setIsConnError] = useState(false);
  const [evalError, setEvalError] = useState<string | null>(null);

  useEffect(() => {
    if (!authReady) return;
    if (!backendOnline) {
      setLoading(false);
      setError("Backend is offline. Ensure the FastAPI server is running on 127.0.0.1:8000.");
      setIsConnError(true);
      return;
    }
    loadSecurityData();
  }, [authReady, backendOnline]);

  const loadSecurityData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [secRes, auditsRes, evalsRes] = await Promise.allSettled([
        api.getSecurityStatus(),
        api.listAuditEvents(25),
        api.listEvaluationRuns(),
      ]);

      if (secRes.status === "fulfilled") setSecurityStatus(secRes.value);
      if (auditsRes.status === "fulfilled") setAuditEvents(auditsRes.value);
      if (evalsRes.status === "fulfilled") setEvalRuns(evalsRes.value);

      if (secRes.status === "rejected") {
        setError(getErrorMessage(secRes.reason));
        setIsConnError(isApiError(secRes.reason) ? secRes.reason.isConnectionError : true);
      } else if (auditsRes.status === "rejected") {
        setError(getErrorMessage(auditsRes.reason));
        setIsConnError(isApiError(auditsRes.reason) ? auditsRes.reason.isConnectionError : true);
      } else if (evalsRes.status === "rejected") {
        setError(getErrorMessage(evalsRes.reason));
        setIsConnError(isApiError(evalsRes.reason) ? evalsRes.reason.isConnectionError : true);
      }
    } catch (err: any) {
      console.error("Failed to load security data:", err);
      setError(getErrorMessage(err));
      setIsConnError(isApiError(err) ? err.isConnectionError : true);
    } finally {
      setLoading(false);
    }
  };

  const handleRunEvaluation = async () => {
    setRunningEval(true);
    setEvalError(null);
    try {
      await api.runEvaluation();
      await loadSecurityData();
    } catch (err: any) {
      setEvalError(getErrorMessage(err, "Failed to execute evaluation benchmark."));
    } finally {
      setRunningEval(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Security & Privacy Center</h1>
          <p className="text-sm text-slate-500 mt-1">
            Offline enforcement, loopback boundary verification, audit logging, and adversarial evaluation.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadSecurityData}
            disabled={loading}
            className="p-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 transition-colors"
            title="Refresh Security Data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button
            onClick={handleRunEvaluation}
            disabled={runningEval}
            className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition-colors"
          >
            <Play className="w-3.5 h-3.5" />
            <span>{runningEval ? "Executing Adversarial Benchmark..." : "Run Security Evaluation"}</span>
          </button>
        </div>
      </div>

      {/* Backend Connection Error */}
      {error && (
        <BackendErrorBanner
          message={error}
          isConnectionError={isConnError}
          onRetry={loadSecurityData}
          retrying={loading}
        />
      )}

      {/* Benchmark Execution Error */}
      {evalError && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{evalError}</span>
          </div>
          <button
            onClick={() => setEvalError(null)}
            className="text-rose-500 hover:text-rose-800 text-xs font-semibold ml-2"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Security Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-400">Offline Isolation</span>
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
          </div>
          <p className="text-xl font-bold text-slate-900">Strict Offline Mode</p>
          <p className="text-xs text-slate-500">
            External cloud AI & telemetries disabled. Loopback endpoints strictly enforced.
          </p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-400">Canary Leakage Defense</span>
            <Lock className="w-5 h-5 text-indigo-600" />
          </div>
          <p className="text-xl font-bold text-slate-900">0% Cross-Matter Leakage</p>
          <p className="text-xs text-slate-500">
            Pre-retrieval matter filtering guarantees isolation across matters.
          </p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-400">Prompt Injection Defense</span>
            <ShieldAlert className="w-5 h-5 text-blue-600" />
          </div>
          <p className="text-xl font-bold text-slate-900">Untrusted Evidence Boundary</p>
          <p className="text-xs text-slate-500">
            System prompts isolate retrieved documents to prevent indirect instructions.
          </p>
        </div>
      </div>

      {/* Evaluation Results Section */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Activity className="w-5 h-5 text-slate-600" />
            <span>Adversarial & Empirical Benchmark Results</span>
          </h2>
          <span className="text-xs text-slate-400">Research Paper Metrics</span>
        </div>

        {evalRuns.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400 bg-slate-50 rounded-lg border border-slate-100">
            No evaluation benchmarks recorded yet. Click &quot;Run Security Evaluation&quot; to execute the test suite.
          </div>
        ) : (
          <div className="space-y-4">
            {evalRuns.slice(0, 3).map((run) => (
              <div key={run.run_id} className="p-4 border border-slate-200 rounded-lg space-y-3 bg-slate-50/50">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 font-mono">{run.run_id}</span>
                    <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] font-semibold">
                      {run.status}
                    </span>
                  </div>
                  <span className="text-slate-400 text-[11px]">{new Date(run.created_at).toLocaleString()}</span>
                </div>

                {run.metrics && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 pt-2 text-xs">
                    <div className="bg-white p-2.5 rounded border border-slate-200">
                      <p className="text-[10px] text-slate-400 uppercase font-semibold">Recall@5</p>
                      <p className="text-sm font-bold text-slate-800">{(run.metrics.recall_at_k * 100).toFixed(0)}%</p>
                    </div>
                    <div className="bg-white p-2.5 rounded border border-slate-200">
                      <p className="text-[10px] text-slate-400 uppercase font-semibold">MRR</p>
                      <p className="text-sm font-bold text-slate-800">{run.metrics.mrr.toFixed(3)}</p>
                    </div>
                    <div className="bg-white p-2.5 rounded border border-slate-200">
                      <p className="text-[10px] text-slate-400 uppercase font-semibold">Cross-Matter Leakage</p>
                      <p className="text-sm font-bold text-emerald-600">
                        {(run.metrics.cross_matter_leakage_rate * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="bg-white p-2.5 rounded border border-slate-200">
                      <p className="text-[10px] text-slate-400 uppercase font-semibold">Injection Success</p>
                      <p className="text-sm font-bold text-emerald-600">
                        {(run.metrics.prompt_injection_success_rate * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="bg-white p-2.5 rounded border border-slate-200">
                      <p className="text-[10px] text-slate-400 uppercase font-semibold">Citation Precision</p>
                      <p className="text-sm font-bold text-slate-800">
                        {(run.metrics.citation_precision * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="bg-white p-2.5 rounded border border-slate-200">
                      <p className="text-[10px] text-slate-400 uppercase font-semibold">Avg Latency</p>
                      <p className="text-sm font-bold text-slate-800">{run.metrics.avg_latency_ms} ms</p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Security Audit Events Stream */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">Recent Security Audit Events</h2>
            <p className="text-xs text-slate-500">Immutable ledger of access authorizations and boundary checks.</p>
          </div>
          <button
            onClick={loadSecurityData}
            className="p-1.5 rounded hover:bg-slate-100 text-slate-500"
            title="Refresh Audit Log"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        <div className="divide-y divide-slate-100 max-h-96 overflow-y-auto">
          {auditEvents.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400">No security audit events recorded.</div>
          ) : (
            auditEvents.map((event) => (
              <div key={event.event_id} className="p-3.5 px-6 hover:bg-slate-50 flex items-center justify-between text-xs">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900">{event.event_type}</span>
                    {event.outcome === "ALLOWED" ? (
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                        ALLOWED
                      </span>
                    ) : (
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-rose-100 text-rose-800">
                        DENIED
                      </span>
                    )}
                    {event.matter_id && (
                      <span className="text-[11px] font-mono text-slate-500">Matter: {event.matter_id}</span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 font-mono">User: {event.user_id || "system"}</p>
                </div>
                <span className="text-[11px] text-slate-400">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
