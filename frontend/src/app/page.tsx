"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText,
  Briefcase,
  ShieldCheck,
  Cpu,
  AlertTriangle,
  ArrowRight,
  Database,
  Search,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { api } from "@/lib/api/client";
import { Matter, SecurityStatus } from "@/types";

export default function DashboardPage() {
  const [matters, setMatters] = useState<Matter[]>([]);
  const [securityStatus, setSecurityStatus] = useState<SecurityStatus | null>(null);
  const [readiness, setReadiness] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [mattersData, secData, readyData] = await Promise.all([
          api.listMatters(),
          api.getSecurityStatus(),
          api.getReadiness().catch((err) => ({ ready: false, subsystems: {} })),
        ]);
        setMatters(mattersData);
        setSecurityStatus(secData);
        setReadiness(readyData);
      } catch (err) {
        console.error("Dashboard data fetch error:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const totalDocuments = matters.reduce((acc, m) => acc + (m.document_count || 0), 0);

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Research Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">
          Local, privacy-preserving legal assistant overview and operational status.
        </p>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
            <Briefcase className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase text-slate-400 tracking-wider">Accessible Matters</p>
            <p className="text-2xl font-bold text-slate-900">{loading ? "..." : matters.length}</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase text-slate-400 tracking-wider">Indexed Documents</p>
            <p className="text-2xl font-bold text-slate-900">{loading ? "..." : totalDocuments}</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase text-slate-400 tracking-wider">Offline State</p>
            <p className="text-sm font-bold text-emerald-700">Enforced & Isolated</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase text-slate-400 tracking-wider">Quarantine Count</p>
            <p className="text-2xl font-bold text-slate-900">
              {loading ? "..." : securityStatus?.quarantine_count || 0}
            </p>
          </div>
        </div>
      </div>

      {/* Subsystem Health Grid */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
        <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <Cpu className="w-5 h-5 text-slate-600" />
          <span>Local Subsystem Readiness</span>
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-1">
          <div className="border border-slate-100 bg-slate-50 p-3.5 rounded-lg flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500">SQLite Metadata Store</p>
              <p className="text-sm font-bold text-slate-800">WAL Mode</p>
            </div>
            {readiness?.subsystems?.sqlite ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            ) : (
              <XCircle className="w-5 h-5 text-rose-600" />
            )}
          </div>

          <div className="border border-slate-100 bg-slate-50 p-3.5 rounded-lg flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500">ChromaDB Vector Store</p>
              <p className="text-sm font-bold text-slate-800">Local Persistent</p>
            </div>
            {readiness?.subsystems?.chromadb ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            ) : (
              <XCircle className="w-5 h-5 text-rose-600" />
            )}
          </div>

          <div className="border border-slate-100 bg-slate-50 p-3.5 rounded-lg flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500">Embedding Engine</p>
              <p className="text-sm font-bold text-slate-800">nomic-embed-text</p>
            </div>
            {readiness?.subsystems?.embedding_model ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            ) : (
              <XCircle className="w-5 h-5 text-rose-600" />
            )}
          </div>

          <div className="border border-slate-100 bg-slate-50 p-3.5 rounded-lg flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500">Inference LLM</p>
              <p className="text-sm font-bold text-slate-800">qwen2.5:1.5b</p>
            </div>
            {readiness?.subsystems?.generation_model ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            ) : (
              <XCircle className="w-5 h-5 text-rose-600" />
            )}
          </div>
        </div>
      </div>

      {/* Accessible Matters Section */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">Your Authorized Legal Matters</h2>
            <p className="text-xs text-slate-500">Matters configured with boundary-enforced isolation.</p>
          </div>
          <Link
            href="/matters"
            className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1"
          >
            Manage Matters <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="p-8 text-center text-sm text-slate-400">Loading authorized matters...</div>
        ) : matters.length === 0 ? (
          <div className="p-8 text-center space-y-3">
            <p className="text-sm text-slate-500">No matters assigned yet.</p>
            <Link
              href="/matters"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-slate-900 text-white rounded-md"
            >
              Create First Matter
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {matters.map((matter) => (
              <div
                key={matter.matter_id}
                className="p-4 sm:px-6 hover:bg-slate-50 transition-colors flex items-center justify-between"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-900 text-sm">{matter.name}</span>
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                      {matter.matter_id}
                    </span>
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                      {matter.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 line-clamp-1">
                    {matter.description || "No description provided."}
                  </p>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right hidden sm:block">
                    <span className="text-xs font-semibold text-slate-700">
                      {matter.document_count || 0} Docs
                    </span>
                  </div>
                  <Link
                    href={`/research?matter=${matter.matter_id}`}
                    className="flex items-center gap-1 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-800 px-3 py-1.5 rounded-md transition-colors"
                  >
                    <Search className="w-3.5 h-3.5 text-slate-600" />
                    <span>Research</span>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
