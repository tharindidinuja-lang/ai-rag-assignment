export type Citation = {
  chunk_id: string;
  page: number | null;
  score: number;
  excerpt: string;
};

export type ChatResponse = {
  answer: string;
  grounded: boolean;
  confidence: number;
  answer_mode: "grounded" | "insufficient_context";
  citations: Citation[];
  retrieved_chunks: number;
  system_notes: string[];
};

export type SystemStatus = {
  status: "ok";
  api_name: string;
  pdf_exists: boolean;
  index_ready: boolean;
  chat_model: string;
  embedding_model: string;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8001";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const maybeJson = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(maybeJson?.detail ?? "The server returned an unexpected error.");
  }

  return (await response.json()) as T;
}

export async function fetchStatus(): Promise<SystemStatus> {
  const response = await fetch(`${API_BASE_URL}/health`, {
    cache: "no-store",
  });

  return handleResponse<SystemStatus>(response);
}

export async function askQuestion(query: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/chat/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query,
      top_k: 4,
      include_sources: true,
    }),
  });

  return handleResponse<ChatResponse>(response);
}

export async function rebuildIndex(): Promise<{ message: string; chunk_count: number }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/ingest/rebuild`, {
    method: "POST",
  });

  return handleResponse<{ message: string; chunk_count: number }>(response);
}
export async function uploadFiles(files: FileList): Promise<any> {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/upload/upload`, {
    method: "POST",
    body: formData,
  });

  return handleResponse<any>(response);
}

export async function listUploadedFiles(): Promise<{ files: Array<{ name: string; size: number; modified: number }> }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/upload/files`);
  return handleResponse<any>(response);
}