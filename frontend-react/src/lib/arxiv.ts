const MODERN_ARXIV_ID_PATTERN = /^(?:arxiv:)?(?<id>\d{4}\.\d{4,5})(?:v\d+)?$/i;
const LEGACY_ARXIV_ID_PATTERN = /^(?:arxiv:)?(?<id>[a-z-]+(?:\.[a-z-]+)?\/\d{7})(?:v\d+)?$/i;

function candidateFromUrl(rawValue: string): string | null {
  try {
    const url = new URL(rawValue);
    const host = url.hostname.toLowerCase();
    if (host !== 'arxiv.org' && !host.endsWith('.arxiv.org')) {
      return null;
    }

    const parts = url.pathname.split('/').filter(Boolean).map(decodeURIComponent);
    if (parts.length < 2 || !['abs', 'pdf', 'html', 'e-print'].includes(parts[0])) {
      return null;
    }

    const candidate = parts.slice(1).join('/');
    return candidate.endsWith('.pdf') ? candidate.slice(0, -4) : candidate;
  } catch {
    return null;
  }
}

export function extractArxivId(rawValue: string): string | null {
  const trimmed = rawValue.trim();
  if (!trimmed) {
    return null;
  }

  let candidate = candidateFromUrl(trimmed) ?? trimmed;
  if (candidate.toLowerCase().startsWith('arxiv:')) {
    candidate = candidate.slice(candidate.indexOf(':') + 1).trim();
  }
  if (candidate.endsWith('.pdf')) {
    candidate = candidate.slice(0, -4);
  }

  const modernMatch = MODERN_ARXIV_ID_PATTERN.exec(candidate);
  if (modernMatch?.groups?.id) {
    return modernMatch.groups.id.toLowerCase();
  }

  const legacyMatch = LEGACY_ARXIV_ID_PATTERN.exec(candidate);
  if (legacyMatch?.groups?.id) {
    return legacyMatch.groups.id.toLowerCase();
  }

  return null;
}
