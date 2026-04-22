"use client";

import { FormEvent, useEffect, useState, useTransition, useRef } from "react";
import {
  askQuestion,
  ChatResponse,
  fetchStatus,
  rebuildIndex,
  SystemStatus,
  uploadFiles,
} from "../lib/api";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: ChatResponse;
};

const STARTER_PROMPTS = [
  "Summarize the PDF.",
  "What major topics are covered in this document?",
  "Explain the main ideas in simple words.",
];

function formatPageReferences(response: ChatResponse): string | null {
  const pages = Array.from(
    new Set(
      response.citations
        .map((citation) => citation.page)
        .filter((page): page is number => page !== null),
    ),
  ).sort((a, b) => a - b);

  if (pages.length === 0) {
    return null;
  }

  if (pages.length === 1) {
    return `Based on page ${pages[0]}`;
  }

  return `Based on pages ${pages.join(", ")}`;
}

export function ChatShell() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let active = true;

    fetchStatus()
      .then((data) => {
        if (active) {
          setStatus(data);
        }
      })
      .catch((err: Error) => {
        if (active) {
          setError(err.message);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    setUploadMessage("Uploading...");

    try {
      const result = await uploadFiles(files);
      setUploadMessage(`✅ ${result.message}`);
      
      // Rebuild index after upload
      await rebuildIndex();
      setUploadMessage(`✅ Upload complete! Index rebuilt. You can now ask questions.`);
      
      // Refresh status
      const nextStatus = await fetchStatus();
      setStatus(nextStatus);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed";
      setUploadMessage(`❌ ${message}`);
    } finally {
      setIsUploading(false);
      // Clear message after 5 seconds
      setTimeout(() => setUploadMessage(null), 5000);
    }
  };

  const submitQuestion = (nextQuery: string) => {
    const cleaned = nextQuery.trim();
    if (!cleaned) {
      return;
    }

    setError(null);
    setQuery("");

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: cleaned,
    };

    setMessages((current) => [...current, userMessage]);

    startTransition(async () => {
      try {
        const response = await askQuestion(cleaned);
        setMessages((current) => [
          ...current,
          {
            id: `assistant-${Date.now()}`,
            role: "assistant",
            content: response.answer,
            response,
          },
        ]);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Something went wrong.";
        setError(message);
      }
    });
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    submitQuestion(query);
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    setError(null);

    try {
      await rebuildIndex();
      const nextStatus = await fetchStatus();
      setStatus(nextStatus);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to refresh the document.";
      setError(message);
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <main className="page-shell">
      <div className="orb orb-left" />
      <div className="orb orb-right" />

      <section className="hero-card minimal">
        <div className="hero-copy">
          <span className="eyebrow">RAG System</span>
          <h1>Ask questions about your document.</h1>
          <p>
            Get clear answers from the PDF in a simple chat
            experience.
          </p>
        </div>

        <div className="status-panel compact">
          <div className="status-copy">
            <strong>
              {status?.index_ready
                ? "Document is ready"
                : "Preparing your document"}
            </strong>
            <p>
              {status?.index_ready
                ? "You can start asking questions now."
                : "If you updated the PDF, refresh the document first."}
            </p>
          </div>
          <button
            className="ghost-button"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            {isRefreshing ? "Refreshing..." : "Refresh document"}
          </button>
        </div>
      </section>

      {/* Upload Section - NEW */}
      <div className="upload-section">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          accept=".pdf,.docx,.txt,.zip"
          multiple
          style={{ display: "none" }}
        />
        <button
          className="upload-button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
        >
          {isUploading ? "⏳ Uploading..." : "📁 Upload Files (PDF, DOCX, TXT, ZIP - max 5MB)"}
        </button>
        {uploadMessage && (
          <p className="upload-message">{uploadMessage}</p>
        )}
      </div>

      <section className="chat-card simple">
        <div className="card-header simple">
          <div>
            <span className="card-label">Chat</span>
            <h2>Ask anything from the PDF.</h2>
          </div>
        </div>

        <div className="starter-row">
          {STARTER_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              className="starter-chip"
              onClick={() => submitQuestion(prompt)}
              type="button"
            >
              {prompt}
            </button>
          ))}
        </div>

        <div className="messages-panel">
          {messages.length === 0 ? (
            <div className="empty-state">
              <p>
                Type a question below and I will answer using the
                PDF.
              </p>
            </div>
          ) : (
            messages.map((message) => {
              const pageReference = message.response
                ? formatPageReferences(message.response)
                : null;

              return (
                <article
                  className={`message-bubble ${message.role === "assistant" ? "assistant" : "user"}`}
                  key={message.id}
                >
                  <span className="message-role">
                    {message.role === "assistant" ? "Assistant" : "You"}
                  </span>
                  <p>{message.content}</p>

                  {message.response && pageReference ? (
                    <p className="page-reference">{pageReference}</p>
                  ) : null}
                </article>
              );
            })
          )}

          {isPending ? (
            <article className="message-bubble assistant loading">
              <span className="message-role">Assistant</span>
              <p>Looking through the PDF...</p>
            </article>
          ) : null}
        </div>

        <form className="composer" onSubmit={handleSubmit}>
          <textarea
            aria-label="Ask a question"
            className="composer-input"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Ask a question about the PDF..."
            rows={3}
            value={query}
          />
          <button
            className="primary-button"
            disabled={isPending || !query.trim()}
            type="submit"
          >
            {isPending ? "Thinking..." : "Send"}
          </button>
        </form>

        {error ? <p className="error-text">{error}</p> : null}
      </section>

      <style jsx>{`
        .upload-section {
          margin: 20px 0;
          text-align: center;
        }
        .upload-button {
          background: #0f766e;
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 999px;
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 180ms ease;
        }
        .upload-button:hover:not(:disabled) {
          background: #115e59;
          transform: translateY(-1px);
        }
        .upload-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        .upload-message {
          margin-top: 10px;
          font-size: 0.875rem;
          color: #64594c;
        }
      `}</style>
    </main>
  );
}