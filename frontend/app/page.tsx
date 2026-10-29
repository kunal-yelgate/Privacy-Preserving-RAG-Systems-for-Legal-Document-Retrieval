"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const USER_ID = process.env.NEXT_PUBLIC_USER_ID ?? "demo-user";

type Matter = { matter_id: string; role: string; client_name?: string; case_title?: string; case_number?: string };
type Document = { document_id: string; filename: string; status: string; quarantine_reason?: string | null };
type Evidence = {
  chunk_id: string;
  document_id: string;
  matter_id: string | null;
  tier: string;
  paragraph: number | null;
};
type Citation = {
  chunk_id: string;
  document_id: string;
  source_name?: string | null;
  matter_id: string | null;
  tier: string;
  paragraph: number | null;
};
type Answer = {
  answer?: string | null;
  abstained?: boolean;
  citations?: Citation[];
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
  const [clientName, setClientName] = useState("");
  const [caseTitle, setCaseTitle] = useState("");
  const [caseNumber, setCaseNumber] = useState("");
  const [caseDescription, setCaseDescription] = useState("");
  const [documents, setDocuments] = useState<Document[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<Answer | null>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [pipelineStep, setPipelineStep] = useState("idle");
  const pipeline = [
    ["upload", "Document", "Upload PDF or DOCX"],
    ["extracted", "Extract", "Read pages and paragraphs"],
    ["retrieving", "Retrieve", "Find authorized evidence"],
    ["answered", "Answer", "Generate cited answer"],
  ];

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
      const created = await api<Matter>(`/matters`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          matter_id: value,
          client_name: clientName.trim() || null,
          case_title: caseTitle.trim() || null,
          case_number: caseNumber.trim() || null,
          case_description: caseDescription.trim() || null,
        }),
      });
      setMatters((current) => [...current, { ...created, matter_id: value, role: "owner" }]);
      setMatterId(value);
      setNewMatterId("");
      setClientName("");
      setCaseTitle("");
      setCaseNumber("");
      setCaseDescription("");
      setMessage(`Case "${value}" is ready for documents.`);
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
      setPipelineStep("extracted");
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
    setPipelineStep("retrieving");
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
      setPipelineStep("answered");
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
            <label htmlFor="new-case">Start a new case</label>
            <div className="inline-form">
              <input id="new-case" value={newMatterId} onChange={(event) => setNewMatterId(event.target.value)} placeholder="e.g. Sharma v State" />
              <button type="submit" disabled={busy || !newMatterId.trim() || !clientName.trim() || !caseTitle.trim()}>Create</button>
            </div>
            <input aria-label="Client name" value={clientName} onChange={(event) => setClientName(event.target.value)} placeholder="Client name" />
            <input aria-label="Case title" value={caseTitle} onChange={(event) => setCaseTitle(event.target.value)} placeholder="Case title" />
            <input aria-label="Case number" value={caseNumber} onChange={(event) => setCaseNumber(event.target.value)} placeholder="Case number (optional)" />
            <textarea aria-label="Case details" value={caseDescription} onChange={(event) => setCaseDescription(event.target.value)} placeholder="Short case details (optional)" />
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
      <section className="pipeline" aria-label="RAG pipeline progress">
        <div className="pipeline-heading"><div><p className="eyebrow">HOW YOUR ANSWER IS BUILT</p><h2>Secure RAG pipeline</h2></div><p>Your documents stay local. Only authorized evidence reaches Ollama.</p></div>
        <div className="pipeline-track">{pipeline.map(([key, title, detail], index) => <div className={`pipeline-step ${pipelineStep === key || (pipelineStep === "answered" && key !== "upload") ? "active" : ""}`} key={key}><span>{index + 1}</span><strong>{title}</strong><small>{detail}</small>{index < pipeline.length - 1 && <i />}</div>)}</div>
      </section>
      {result && <section className="answer">
        <p className="eyebrow">GROUNDED ANSWER</p>
        {result.abstained || !result.answer ? <h2>There is not enough supporting evidence to answer safely.</h2> : <p className="answer-text">{result.answer}</p>}
        {!!result.citations?.length && <div className="sources"><strong>Cited sources</strong>{[...new Map(result.citations.map((citation) => [citation.chunk_id, citation])).values()].map((citation) => {
          const document = documents.find((item) => item.document_id === citation.document_id);
          return <span key={citation.chunk_id}>{document?.filename ?? citation.source_name ?? `Document ${citation.document_id}`}{citation.paragraph ? ` · paragraph ${citation.paragraph}` : ""}</span>;
        })}</div>}
      </section>}
      <footer>Research support only — not legal advice. Your documents stay within this local system.</footer>
    </main>
  );
}
