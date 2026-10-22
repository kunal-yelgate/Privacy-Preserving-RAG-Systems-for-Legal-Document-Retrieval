"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Briefcase,
  Plus,
  FileText,
  Search,
  Trash2,
  Calendar,
  User,
  Shield,
  CheckCircle,
} from "lucide-react";
import { api } from "@/lib/api/client";
import { Matter } from "@/types";

export default function MattersPage() {
  const [matters, setMatters] = useState<Matter[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [matterId, setMatterId] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [clientName, setClientName] = useState("");
  const [leadCounsel, setLeadCounsel] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadMatters();
  }, []);

  const loadMatters = async () => {
    setLoading(true);
    try {
      const data = await api.listMatters();
      setMatters(data);
    } catch (err) {
      console.error("Failed to load matters:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!matterId || !name) return;

    setSubmitting(true);
    try {
      await api.createMatter({
        matter_id: matterId.toLowerCase().trim(),
        name: name.trim(),
        description: description.trim() || undefined,
        client_name: clientName.trim() || undefined,
        lead_counsel: leadCounsel.trim() || undefined,
      });
      setShowCreateModal(false);
      setMatterId("");
      setName("");
      setDescription("");
      setClientName("");
      setLeadCounsel("");
      await loadMatters();
    } catch (err: any) {
      alert(err.message || "Failed to create matter.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Legal Matters</h1>
          <p className="text-sm text-slate-500 mt-1">
            Matters enforce strict retrieval boundaries and confidential client isolation.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>New Matter</span>
        </button>
      </div>

      {loading ? (
        <div className="p-12 text-center text-sm text-slate-400">Loading matters...</div>
      ) : matters.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center space-y-3">
          <Briefcase className="w-10 h-10 text-slate-300 mx-auto" />
          <p className="text-sm text-slate-600 font-medium">No legal matters configured.</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-3 py-1.5 text-xs font-semibold bg-slate-900 text-white rounded-md"
          >
            Create Your First Matter
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {matters.map((matter) => (
            <div
              key={matter.matter_id}
              className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col justify-between hover:border-slate-300 transition-colors"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-semibold">
                      {matter.matter_id}
                    </span>
                    <h3 className="font-bold text-slate-900 text-base leading-snug">{matter.name}</h3>
                  </div>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                    {matter.status}
                  </span>
                </div>

                <p className="text-xs text-slate-500 line-clamp-2">
                  {matter.description || "No description provided."}
                </p>

                <div className="pt-2 border-t border-slate-100 space-y-1.5 text-xs text-slate-600">
                  {matter.client_name && (
                    <div className="flex items-center gap-1.5">
                      <User className="w-3.5 h-3.5 text-slate-400" />
                      <span>Client: {matter.client_name}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-slate-400" />
                    <span>{matter.document_count || 0} Documents Indexed</span>
                  </div>
                </div>
              </div>

              <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between">
                <Link
                  href={`/documents?matter=${matter.matter_id}`}
                  className="text-xs font-semibold text-slate-600 hover:text-slate-900"
                >
                  View Documents
                </Link>
                <Link
                  href={`/research?matter=${matter.matter_id}`}
                  className="flex items-center gap-1 text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-white px-3 py-1.5 rounded-md transition-colors"
                >
                  <Search className="w-3.5 h-3.5" />
                  <span>Research</span>
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-md w-full p-6 space-y-5">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-slate-900">Create New Legal Matter</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg leading-none"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Matter Identifier (ID)
                </label>
                <input
                  type="text"
                  placeholder="e.g. matter-101"
                  value={matterId}
                  onChange={(e) => setMatterId(e.target.value)}
                  className="w-full text-xs font-mono border border-slate-200 rounded-lg p-2 focus:ring-1 focus:ring-slate-900 focus:outline-none"
                  required
                />
                <p className="text-[10px] text-slate-400 mt-0.5">Alphanumeric, hyphens and underscores only.</p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Matter Name / Case Title
                </label>
                <input
                  type="text"
                  placeholder="e.g. Apex Corp v. Nexus Tech"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full text-xs border border-slate-200 rounded-lg p-2 focus:ring-1 focus:ring-slate-900 focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Description
                </label>
                <textarea
                  placeholder="Brief summary of matter scope..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  className="w-full text-xs border border-slate-200 rounded-lg p-2 focus:ring-1 focus:ring-slate-900 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Client Name (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Nexus Legal Systems"
                  value={clientName}
                  onChange={(e) => setClientName(e.target.value)}
                  className="w-full text-xs border border-slate-200 rounded-lg p-2 focus:ring-1 focus:ring-slate-900 focus:outline-none"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-md"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-1.5 text-xs font-semibold bg-slate-900 text-white rounded-md hover:bg-slate-800 disabled:opacity-50"
                >
                  {submitting ? "Creating..." : "Create Matter"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
