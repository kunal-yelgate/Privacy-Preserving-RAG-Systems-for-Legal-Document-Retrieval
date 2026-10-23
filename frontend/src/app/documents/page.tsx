"use client";

import React, { useEffect, useState } from "react";
import {
  FileText,
  Upload,
  Trash2,
  AlertCircle,
  CheckCircle,
  Clock,
  Filter,
  Plus,
  RefreshCw,
} from "lucide-react";
import { api, getErrorMessage, isApiError } from "@/lib/api/client";
import { ClassificationLevel, DocumentMetadata, Matter } from "@/types";
import { BackendErrorBanner } from "@/components/ui/BackendErrorBanner";
import { useAuth } from "@/contexts/AuthContext";

export default function DocumentsPage() {
  const { authReady, backendOnline } = useAuth();
  const [matters, setMatters] = useState<Matter[]>([]);
  const [selectedMatter, setSelectedMatter] = useState<string>("");
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConnError, setIsConnError] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Upload modal state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadClassification, setUploadClassification] = useState<ClassificationLevel>("confidential");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const fetchMatters = async () => {
    setError(null);
    try {
      const m = await api.listMatters();
      setMatters(m);
      if (m.length > 0 && !selectedMatter) {
        setSelectedMatter(m[0].matter_id);
      }
    } catch (err: any) {
      console.error("Failed to load matters:", err);
      setError(getErrorMessage(err));
      setIsConnError(isApiError(err) ? err.isConnectionError : true);
    }
  };

  useEffect(() => {
    if (!authReady) return;
    if (!backendOnline) {
      setError("Backend is offline. Ensure the FastAPI server is running on 127.0.0.1:8000.");
      setIsConnError(true);
      return;
    }
    fetchMatters();
  }, [authReady, backendOnline]);

  useEffect(() => {
    if (!selectedMatter) return;
    loadDocuments(selectedMatter);
  }, [selectedMatter]);

  const loadDocuments = async (matterId: string) => {
    if (!matterId) return;
    setLoading(true);
    setActionError(null);
    try {
      const docs = await api.listDocuments(matterId);
      setDocuments(docs);
      setError(null);
    } catch (err: any) {
      console.error("Failed to load documents:", err);
      setError(getErrorMessage(err));
      setIsConnError(isApiError(err) ? err.isConnectionError : true);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !selectedMatter) return;

    setUploading(true);
    setUploadError(null);
    try {
      await api.uploadDocument(uploadFile, selectedMatter, uploadTitle, uploadClassification);
      setShowUploadModal(false);
      setUploadFile(null);
      setUploadTitle("");
      await loadDocuments(selectedMatter);
    } catch (err: any) {
      setUploadError(getErrorMessage(err, "Upload failed."));
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId: string) => {
    if (!confirm("Are you sure you want to delete this document? Chunks and embeddings will also be removed.")) {
      return;
    }
    setActionError(null);
    try {
      await api.deleteDocument(docId);
      await loadDocuments(selectedMatter);
    } catch (err: any) {
      setActionError(getErrorMessage(err, "Failed to delete document."));
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Document Management</h1>
          <p className="text-sm text-slate-500 mt-1">
            Ingest and manage legal PDFs and TXT files with page-level provenance.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition-colors"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Document</span>
          </button>
        </div>
      </div>

      {/* Error Alert Banners */}
      {error && (
        <BackendErrorBanner
          message={error}
          isConnectionError={isConnError}
          onRetry={() => {
            fetchMatters();
            if (selectedMatter) loadDocuments(selectedMatter);
          }}
          retrying={loading}
        />
      )}

      {actionError && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{actionError}</span>
          </div>
          <button
            onClick={() => setActionError(null)}
            className="text-rose-500 hover:text-rose-800 text-xs font-semibold ml-2"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Matter Selector Filter */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
        <Filter className="w-4 h-4 text-slate-400" />
        <span className="text-xs font-semibold text-slate-700">Filter by Matter:</span>
        <select
          value={selectedMatter}
          onChange={(e) => setSelectedMatter(e.target.value)}
          className="text-xs font-medium border border-slate-200 rounded-md px-3 py-1.5 bg-slate-50 text-slate-800 focus:outline-none focus:ring-1 focus:ring-slate-900"
        >
          {matters.length === 0 && <option value="">No matters available</option>}
          {matters.map((m) => (
            <option key={m.matter_id} value={m.matter_id}>
              {m.name} ({m.matter_id})
            </option>
          ))}
        </select>
        <button
          onClick={() => {
            if (selectedMatter) loadDocuments(selectedMatter);
            else fetchMatters();
          }}
          className="ml-auto p-1.5 rounded-md hover:bg-slate-100 text-slate-500 transition-colors"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Documents Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-sm text-slate-400">Loading documents...</div>
        ) : error && documents.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
            <p className="text-sm text-rose-800 font-semibold">Unable to fetch documents from backend</p>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Please ensure the FastAPI service is active and responsive on 127.0.0.1:8000.
            </p>
            <button
              onClick={() => {
                fetchMatters();
                if (selectedMatter) loadDocuments(selectedMatter);
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-slate-900 text-white rounded-md hover:bg-slate-800"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Request</span>
            </button>
          </div>
        ) : documents.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <FileText className="w-10 h-10 text-slate-300 mx-auto" />
            <p className="text-sm text-slate-600 font-medium">No documents uploaded for this matter yet.</p>
            <p className="text-xs text-slate-400">Supported formats: PDF (selectable text), TXT.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200 uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="py-3 px-4">Title & Filename</th>
                  <th className="py-3 px-4">Classification</th>
                  <th className="py-3 px-4">Ingestion Status</th>
                  <th className="py-3 px-4">Pages / Chunks</th>
                  <th className="py-3 px-4">Size</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {documents.map((doc) => (
                  <tr key={doc.document_id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3.5 px-4 font-medium text-slate-900">
                      <div>
                        <p className="font-semibold text-sm">{doc.title}</p>
                        <p className="text-[11px] font-mono text-slate-400">{doc.original_filename}</p>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase bg-slate-100 text-slate-700 border border-slate-200">
                        {doc.classification}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      {doc.status === "completed" ? (
                        <span className="flex items-center gap-1.5 text-emerald-700 font-medium">
                          <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
                          <span>Indexed</span>
                        </span>
                      ) : doc.status === "failed" ? (
                        <span
                          className="flex items-center gap-1.5 text-rose-700 font-medium"
                          title={doc.error_message || "Ingestion error"}
                        >
                          <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
                          <span>Failed</span>
                        </span>
                      ) : (
                        <span className="flex items-center gap-1.5 text-amber-700 font-medium">
                          <Clock className="w-3.5 h-3.5 text-amber-500 animate-spin" />
                          <span className="capitalize">{doc.status}</span>
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-[11px]">
                      {doc.total_pages} pages / {doc.total_chunks} chunks
                    </td>
                    <td className="py-3.5 px-4 text-slate-500 font-mono text-[11px]">
                      {(doc.file_size_bytes / 1024).toFixed(1)} KB
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => handleDelete(doc.document_id)}
                        className="text-slate-400 hover:text-rose-600 p-1.5 rounded hover:bg-slate-100 transition-colors"
                        title="Delete document and vector index"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-md w-full p-6 space-y-5">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-slate-900">Upload Legal Document</h2>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg leading-none"
              >
                &times;
              </button>
            </div>

            {uploadError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}

            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Target Matter
                </label>
                <select
                  value={selectedMatter}
                  onChange={(e) => setSelectedMatter(e.target.value)}
                  className="w-full text-xs border border-slate-200 rounded-lg p-2 bg-slate-50"
                  required
                >
                  {matters.map((m) => (
                    <option key={m.matter_id} value={m.matter_id}>
                      {m.name} ({m.matter_id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Document Title (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Master Services Agreement"
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  className="w-full text-xs border border-slate-200 rounded-lg p-2 focus:ring-1 focus:ring-slate-900 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Classification Level
                </label>
                <select
                  value={uploadClassification}
                  onChange={(e) => setUploadClassification(e.target.value as ClassificationLevel)}
                  className="w-full text-xs border border-slate-200 rounded-lg p-2 bg-slate-50"
                >
                  <option value="confidential">Confidential</option>
                  <option value="highly_confidential">Highly Confidential</option>
                  <option value="internal">Internal</option>
                  <option value="public">Public</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Select File (.pdf, .txt)
                </label>
                <input
                  type="file"
                  accept=".pdf,.txt"
                  onChange={(e) => setUploadFile(e.target.files ? e.target.files[0] : null)}
                  className="w-full text-xs file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200"
                  required
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-md"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="px-4 py-1.5 text-xs font-semibold bg-slate-900 text-white rounded-md hover:bg-slate-800 disabled:opacity-50"
                >
                  {uploading ? "Ingesting..." : "Start Ingestion"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
