"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const USER_ID = process.env.NEXT_PUBLIC_USER_ID ?? "demo-user";

type Matter = { matter_id: string; role: string };
type Document = { document_id: string; filename: string; status: string; quarantine_reason?: string | null };
type Evidence = {
  chunk_id: string;
  document_id: string;
  matter_id: string | null;
  page: number | null;
  paragraph: number | null;
};
type Answer = {
  answer?: string | null;
  abstained?: boolean;
  evidence?: Evidence[];
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "X-User-Id": USER_ID, ...(init?.headers ?? {}) },
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body?.detail;
    const message = typeof detail === "object" ? detail.message ?? detail.error : detail;
    throw new Error(message || `Request failed (${response.status})`);
  }
  return body as T;
}

export default function Home() {
  const [matters, setMatters] = useState<Matter[]>([]);
  const [matterId, setMatterId] = useState("");
  const [newMatterId, setNewMatterId] = useState("");
  const [documents, setDocuments] = useState<Document[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<Answer | null>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api<{ matters: Matter[] }>("/matters")
      .then(({ matters: available }) => {
        setMatters(available);
        if (available[0]) setMatterId(available[0].matter_id);
      })
      .catch((error: Error) => setMessage(error.message));
  }, []);

  useEffect(() => {
    if (!matterId) {
      setDocuments([]);
      return;
    }
    api<{ documents: Document[] }>(`/matters/${encodeURIComponent(matterId)}/documents`)
      .then(({ documents: available }) => setDocuments(available))
      .catch((error: Error) => setMessage(error.message));
  }, [matterId]);

  async function createMatter(event: FormEvent) {
    event.preventDefault();
    const value = newMatterId.trim();
    if (!value) return setMessage("Enter a name for your case.");
    setBusy(true);
    try {
      await api(`/matters`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ matter_id: value }),
      });
      setMatters((current) => [...current, { matter_id: value, role: "owner" }]);
      setMatterId(value);
      setNewMatterId("");
      setMessage(`Case "${value}" is ready.`);
    } catch (error) {
      setMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function upload(event: FormEvent) {
    event.preventDefault();
    if (!file || !matterId) return setMessage("Choose a case and a document first.");
    setBusy(true);
    setMessage("");
    try {
      const body = new FormData();
      body.append("file", file);
      const response = await api<{ status: string; quarantine_reason?: string }>(
        `/matters/${encodeURIComponent(matterId)}/documents`,
        { method: "POST", body },
      );
      setMessage(
        response.status === "indexed"
          ? `${file.name} is ready for questions.`
          : `This document was not indexed: ${response.quarantine_reason ?? response.status}`,
      );
      setFile(null);
      const { documents: available } = await api<{ documents: Document[] }>(
        `/matters/${encodeURIComponent(matterId)}/documents`,
      );
      setDocuments(available);
    } catch (error) {
      setMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function ask(event: FormEvent) {
    event.preventDefault();
    if (!question.trim()) return setMessage("Type a question about your case.");
    setBusy(true);
    setMessage("");
    try {
      setResult(
        await api<Answer>("/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question,
            scope: { public: true, matter_ids: matterId ? [matterId] : [] },
          }),
        }),
      );
    } catch (error) {
      setMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell">
      <header className="header">
        <div className="brand"><span className="mark">C</span><span>Casewise</span></div>
        <span className="privacy">Private by design</span>
      </header>
      <section className="hero">
        <p className="eyebrow">YOUR LEGAL RESEARCH ASSISTANT</p>
        <h1>Understand your case,<br /><em>with confidence.</em></h1>
        <p className="intro">Upload your case documents, then ask questions in plain language. Answers are grounded in your authorized documents and show their sources.</p>
      </section>
      {message && <div className="notice" role="status">{message}</div>}
      <section className="workspace">
        <div className="card">
          <div className="card-title"><span className="number">01</span><div><h2>Choose your case</h2><p>Select where your documents belong.</p></div></div>
          <label htmlFor="matter">Case</label>
          <select id="matter" value={matterId} onChange={(event) => setMatterId(event.target.value)}>
            {matters.length === 0 && <option value="">No cases available</option>}
            {matters.map((matter) => <option key={matter.matter_id} value={matter.matter_id}>{matter.matter_id}</option>)}
          </select>
          <form className="new-case" onSubmit={createMatter}>
            <label htmlFor="new-case">Or start a new case</label>
            <div className="inline-form">
              <input id="new-case" value={newMatterId} onChange={(event) => setNewMatterId(event.target.value)} placeholder="e.g. Sharma v State" />
              <button type="submit" disabled={busy || !newMatterId.trim()}>Create</button>
            </div>
          </form>
        </div>
        <form className="card upload-card" onSubmit={upload}>
          <div className="card-title"><span className="number">02</span><div><h2>Add your documents</h2><p>PDF or Word files are supported.</p></div></div>
          <label className="dropzone" htmlFor="document">
            <span className="upload-icon">↑</span>
            <strong>{file ? file.name : "Choose a document"}</strong>
            <small>{file ? "Ready to upload" : "or drag and drop it here"}</small>
            <input id="document" type="file" accept=".pdf,.docx" onChange={(event: ChangeEvent<HTMLInputElement>) => setFile(event.target.files?.[0] ?? null)} />
          </label>
          <button type="submit" disabled={busy || !file || !matterId}>{busy ? "Working..." : "Upload document"}</button>
          {documents.length > 0 && <div className="document-list"><strong>Documents in this case</strong>{documents.map((document) => <span key={document.document_id}>{document.filename} · {document.status}</span>)}</div>}
        </form>
        <form className="card ask-card" onSubmit={ask}>
          <div className="card-title"><span className="number">03</span><div><h2>Ask your question</h2><p>Get a clear answer with supporting sources.</p></div></div>
          <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="For example: What evidence supports the contract breach claim?" />
          <button type="submit" disabled={busy || !question.trim()}>{busy ? "Researching..." : "Find my answer  →"}</button>
        </form>
      </section>
      {result && <section className="answer">
        <p className="eyebrow">GROUNDED ANSWER</p>
        {result.abstained || !result.answer ? <h2>There is not enough supporting evidence to answer safely.</h2> : <p className="answer-text">{result.answer}</p>}
        {!!result.evidence?.length && <div className="sources"><strong>Sources checked</strong>{result.evidence.map((item) => <span key={item.chunk_id}>{item.document_id}{item.page ? ` · page ${item.page}` : ""}</span>)}</div>}
      </section>}
      <footer>Research support only — not legal advice. Your documents stay within this local system.</footer>
    </main>
  );
}
