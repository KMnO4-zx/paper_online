import type {
  ChatMessage,
  ChatSessionSummary,
  OnlineCount,
  Paper,
  PaperListResponse,
  SearchFilters,
} from '@/types';

const API_BASE = import.meta.env.DEV ? 'http://127.0.0.1:8000' : '';

interface StreamOptions {
  onChunk?: (chunk: string) => void;
  onEvent?: (event: string, data: string) => void;
}

function buildSearchRequestParams(
  page: number,
  query: string,
  filters: SearchFilters,
): URLSearchParams {
  const params = new URLSearchParams({
    page: String(page),
    limit: '8',
  });

  if (query.trim()) {
    params.set('search', query.trim());
    params.set('search_title', String(filters.title));
    params.set('search_abstract', String(filters.abstract));
    params.set('search_keywords', String(filters.keywords));
  }

  return params;
}

async function readJson<T>(response: Response): Promise<T> {
  if (response.ok) {
    return (await response.json()) as T;
  }

  let detail = 'Request failed';
  try {
    const parsed = (await response.json()) as { detail?: string };
    detail = parsed.detail ?? detail;
  } catch {
    detail = response.statusText || detail;
  }
  throw new Error(detail);
}

export async function fetchPaperInfo(paperId: string): Promise<Paper> {
  const response = await fetch(`${API_BASE}/paper/${paperId}/info`);
  return readJson<Paper>(response);
}

export async function fetchConferencePapers(
  venue: string,
  page: number,
  query: string,
  filters: SearchFilters,
): Promise<PaperListResponse> {
  const params = buildSearchRequestParams(page, query, filters);
  const response = await fetch(`${API_BASE}/conference/${venue}/papers?${params.toString()}`);
  return readJson<PaperListResponse>(response);
}

export async function fetchSearchPapers(
  page: number,
  query: string,
  filters: SearchFilters,
): Promise<PaperListResponse> {
  const params = buildSearchRequestParams(page, query, filters);
  const response = await fetch(`${API_BASE}/search/papers?${params.toString()}`);
  return readJson<PaperListResponse>(response);
}

export async function fetchChatSessions(paperId: string, userId: string): Promise<ChatSessionSummary[]> {
  const response = await fetch(`${API_BASE}/paper/${paperId}/chat/sessions?user_id=${encodeURIComponent(userId)}`);
  return readJson<ChatSessionSummary[]>(response);
}

export async function fetchChatMessages(sessionId: string): Promise<ChatMessage[]> {
  const response = await fetch(`${API_BASE}/chat/${sessionId}/messages`);
  return readJson<ChatMessage[]>(response);
}

export async function deleteChatSession(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/chat/${sessionId}`, { method: 'DELETE' });
  await readJson<{ ok: boolean }>(response);
}

export async function fetchOnlineCount(): Promise<number> {
  const response = await fetch(`${API_BASE}/online/count`);
  const payload = await readJson<OnlineCount>(response);
  return payload.count;
}

export async function sendHeartbeat(userId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/online/heartbeat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId }),
  });
  await readJson<{ status: string }>(response);
}

function dispatchEvent(block: string, handlers: StreamOptions): void {
  if (!block.trim()) {
    return;
  }

  let eventName = 'message';
  const dataLines: string[] = [];

  for (const line of block.split('\n')) {
    if (line.startsWith('event:')) {
      eventName = line.slice(6).trim() || 'message';
      continue;
    }

    if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trimStart());
    }
  }

  const payload = dataLines.join('\n');
  if (eventName === 'message' && payload) {
    handlers.onChunk?.(payload);
  }
  handlers.onEvent?.(eventName, payload);
}

export async function streamSse(
  input: RequestInfo | URL,
  init: RequestInit,
  handlers: StreamOptions,
): Promise<void> {
  const request = typeof input === 'string' && input.startsWith('/') ? `${API_BASE}${input}` : input;
  const response = await fetch(request, init);
  if (!response.ok) {
    throw new Error(response.statusText || 'Stream request failed');
  }

  if (!response.body) {
    throw new Error('Streaming is not supported in this browser');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true }).replaceAll('\r\n', '\n');
    const parts = buffer.split('\n\n');
    buffer = parts.pop() ?? '';
    for (const part of parts) {
      dispatchEvent(part, handlers);
    }
  }

  if (buffer.trim()) {
    dispatchEvent(buffer, handlers);
  }
}
