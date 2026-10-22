"use client";

import React, { useState } from "react";
import { Settings as SettingsIcon, Cpu, Sliders, Shield, Terminal, CheckCircle2 } from "lucide-react";

export default function SettingsPage() {
  const [topK, setTopK] = useState(5);
  const [chunkSize, setChunkSize] = useState(600);
  const [chunkOverlap, setChunkOverlap] = useState(100);
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">System Settings</h1>
        <p className="text-sm text-slate-500 mt-1">
          Configure local inference models, chunking hyperparameters, and inspect offline boundaries.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Model Configurations */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-slate-600" />
            <span>Local Inference Engines (Ollama)</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Embedding Model</label>
              <input
                type="text"
                value="nomic-embed-text"
                disabled
                className="w-full border border-slate-200 bg-slate-50 rounded-lg p-2 font-mono text-slate-600 cursor-not-allowed"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                768-dimensional local embedding model optimized for technical & legal search.
              </p>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Generation Model</label>
              <input
                type="text"
                value="qwen2.5:1.5b"
                disabled
                className="w-full border border-slate-200 bg-slate-50 rounded-lg p-2 font-mono text-slate-600 cursor-not-allowed"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                Quantized 1.5B parameter local LLM tailored for low-memory 8 GB RAM machines.
              </p>
            </div>
          </div>
        </div>

        {/* Hyperparameters */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Sliders className="w-5 h-5 text-slate-600" />
            <span>Retrieval & Chunking Hyperparameters</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Retrieval Top-K</label>
              <input
                type="number"
                min={1}
                max={20}
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-full border border-slate-200 rounded-lg p-2 font-mono"
              />
              <p className="text-[11px] text-slate-400 mt-1">Number of hybrid chunks passed to generation.</p>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Chunk Size (chars)</label>
              <input
                type="number"
                min={200}
                max={2000}
                value={chunkSize}
                onChange={(e) => setChunkSize(Number(e.target.value))}
                className="w-full border border-slate-200 rounded-lg p-2 font-mono"
              />
              <p className="text-[11px] text-slate-400 mt-1">Target character length per legal passage.</p>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Chunk Overlap (chars)</label>
              <input
                type="number"
                min={20}
                max={500}
                value={chunkOverlap}
                onChange={(e) => setChunkOverlap(Number(e.target.value))}
                className="w-full border border-slate-200 rounded-lg p-2 font-mono"
              />
              <p className="text-[11px] text-slate-400 mt-1">Sliding window overlap between chunks.</p>
            </div>
          </div>

          <div className="pt-2 flex items-center justify-between">
            {saved && (
              <span className="text-xs text-emerald-600 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4" /> Parameters saved for active session.
              </span>
            )}
            <button
              type="submit"
              className="ml-auto px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
            >
              Update Hyperparameters
            </button>
          </div>
        </div>

        {/* Read-Only Security Configurations */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Shield className="w-5 h-5 text-slate-600" />
            <span>Read-Only Privacy Boundaries</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div className="bg-slate-50 border border-slate-200 p-3 rounded-lg space-y-0.5">
              <span className="font-semibold text-slate-700">API Loopback Binding</span>
              <p className="text-[11px] font-mono text-slate-500">127.0.0.1:8000 (Loopback Only)</p>
            </div>

            <div className="bg-slate-50 border border-slate-200 p-3 rounded-lg space-y-0.5">
              <span className="font-semibold text-slate-700">Telemetry & Cloud Fallbacks</span>
              <p className="text-[11px] font-mono text-emerald-700 font-bold">DISABLED (100% Offline)</p>
            </div>

            <div className="bg-slate-50 border border-slate-200 p-3 rounded-lg space-y-0.5">
              <span className="font-semibold text-slate-700">SQLite Journal Mode</span>
              <p className="text-[11px] font-mono text-slate-500">WAL (Write-Ahead Logging)</p>
            </div>

            <div className="bg-slate-50 border border-slate-200 p-3 rounded-lg space-y-0.5">
              <span className="font-semibold text-slate-700">Vector Collection Space</span>
              <p className="text-[11px] font-mono text-slate-500">HNSW Cosine Distance (ChromaDB)</p>
            </div>
          </div>
        </div>

        {/* Model Download Instructions */}
        <div className="bg-slate-900 text-white rounded-xl p-6 space-y-3 shadow-sm">
          <h3 className="text-sm font-bold flex items-center gap-2">
            <Terminal className="w-4 h-4 text-emerald-400" />
            <span>Preparing Offline Models via PowerShell</span>
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            Before disconnecting internet connectivity or operating in an air-gapped environment, ensure both
            required models have been pulled into your local Ollama cache:
          </p>
          <div className="bg-slate-950 p-3 rounded-lg font-mono text-xs text-emerald-400 space-y-1">
            <p>ollama pull nomic-embed-text</p>
            <p>ollama pull qwen2.5:1.5b</p>
          </div>
          <p className="text-[11px] text-slate-400">
            Once downloaded, all embeddings, keyword searches, vector queries, and answer generation will function
            100% offline with zero outbound network requests.
          </p>
        </div>
      </form>
    </div>
  );
}
